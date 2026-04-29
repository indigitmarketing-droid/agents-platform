"""Real Setting Agent. Replaces setting_stub."""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from packages.agent_framework import BaseAgent, FatalError
from packages.agent_framework.supabase_client import create_supabase_client

from apps.workers.setting_agent.claude_client import create_anthropic_client
from apps.workers.setting_agent.elevenlabs_client import (
    create_elevenlabs_client,
    ElevenLabsError,
)
from apps.workers.setting_agent.lead_picker import pick_leads_for_batch
from apps.workers.setting_agent.transcript_analyzer import (
    analyze_transcript,
    AnalysisError,
)
from apps.workers.setting_agent.compliance import (
    is_within_business_hours,
    is_phone_in_dnc,
    US_TIMEZONE,
)

logger = logging.getLogger(__name__)


class SettingAgent(BaseAgent):
    """
    Real voice Setting Agent.

    Triggers daily batch of cold calls (10am ET, max 10/day, US only).
    Receives webhook (via setting.call_completed event) → Claude analyze →
    emits setting.call_accepted (target=builder) or setting.call_rejected.
    """

    SCHEDULER_TICK_SECONDS = 60
    BATCH_HOUR_LOCAL = 10
    DAILY_CALL_LIMIT = 10
    ORPHAN_CHECK_INTERVAL = 3600
    ORPHAN_THRESHOLD_MINUTES = 30
    MAX_CALL_ATTEMPTS = 3

    def __init__(self, **kwargs):
        super().__init__(agent_id="setting", **kwargs)
        try:
            self._claude = create_anthropic_client()
        except KeyError:
            logger.warning("ANTHROPIC_API_KEY not set; transcript analysis will fail")
            self._claude = None
        try:
            self._elevenlabs = create_elevenlabs_client()
        except KeyError:
            logger.warning("ELEVENLABS_API_KEY not set; outbound calls will fail")
            self._elevenlabs = None

        self._agent_id_voice = os.environ.get("ELEVENLABS_AGENT_ID", "")
        self._agent_phone_id = os.environ.get("ELEVENLABS_AGENT_PHONE_NUMBER_ID", "")
        self._last_batch_date = None

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        if event_type == "setting.call_completed":
            return await self._handle_call_completed(event)
        if event_type == "builder.website_ready":
            logger.info(
                f"builder.website_ready for lead {event.get('payload', {}).get('lead_id')}; "
                "site-ready call is phase 2, skipping."
            )
            return []
        return []

    async def _handle_call_completed(self, event: dict) -> list[dict]:
        payload = event.get("payload", {})
        conversation_id = payload.get("conversation_id")
        transcript = payload.get("transcript", "")
        lead_id = payload.get("lead_id")

        if not conversation_id or not lead_id:
            raise FatalError(f"call_completed missing required fields: {payload}")

        call_log = self._load_call_log(conversation_id)
        if call_log is None:
            logger.warning(f"call_log not found for {conversation_id}; analyzing anyway")
            call_log = {"id": None, "lead_id": lead_id, "phone": None}

        lead = self._load_lead(lead_id)
        if lead is None:
            raise FatalError(f"lead {lead_id} not found")

        try:
            analysis = analyze_transcript(transcript, lead, self._claude)
        except AnalysisError as e:
            logger.error(f"Transcript analysis failed for {conversation_id}: {e}")
            self._update_call_log(call_log["id"], outcome="unclear")
            self._update_lead(lead_id, call_status="never_called")
            return [{
                "type": "setting.call_unclear",
                "target_agent": None,
                "payload": {
                    "lead_id": lead_id,
                    "transcript_excerpt": transcript[:200] if transcript else "",
                },
            }]

        outcome = analysis["outcome"]
        opt_out = analysis.get("opt_out", False)
        call_brief = analysis.get("call_brief")

        self._update_call_log(call_log["id"], outcome=outcome, call_brief=call_brief)

        if opt_out and call_log.get("phone"):
            self._add_to_dnc(call_log["phone"], reason="lead_request")
            self._update_lead(lead_id, call_status="do_not_call")
        else:
            new_status = outcome if outcome in ("accepted", "rejected") else "never_called"
            self._update_lead(lead_id, call_status=new_status)

        if outcome == "accepted":
            return [{
                "type": "setting.call_accepted",
                "target_agent": "builder",
                "payload": {
                    "lead_id": lead_id,
                    "lead": lead,
                    "call_brief": call_brief,
                },
            }]
        if outcome == "rejected":
            return [{
                "type": "setting.call_rejected",
                "target_agent": None,
                "payload": {"lead_id": lead_id, "reason": "lead declined"},
            }]
        return [{
            "type": "setting.call_unclear",
            "target_agent": None,
            "payload": {
                "lead_id": lead_id,
                "transcript_excerpt": transcript[:200] if transcript else "",
            },
        }]

    def _load_call_log(self, conversation_id: str):
        result = (
            self._client.table("call_logs")
            .select("*")
            .eq("conversation_id", conversation_id)
            .maybe_single()
            .execute()
        )
        return result.data

    def _load_lead(self, lead_id: str):
        result = (
            self._client.table("leads")
            .select("*")
            .eq("id", lead_id)
            .maybe_single()
            .execute()
        )
        return result.data

    def _update_call_log(self, call_log_id, outcome=None, call_brief=None, status=None, error=None):
        if call_log_id is None:
            return
        updates = {"analyzed_at": datetime.now(timezone.utc).isoformat()}
        if outcome is not None:
            updates["outcome"] = outcome
        if call_brief is not None:
            updates["call_brief"] = call_brief
        if status is not None:
            updates["status"] = status
        if error is not None:
            updates["error"] = error
        self._client.table("call_logs").update(updates).eq("id", call_log_id).execute()

    def _update_lead(self, lead_id: str, **fields):
        self._client.table("leads").update(fields).eq("id", lead_id).execute()

    def _add_to_dnc(self, phone: str, reason: str):
        try:
            self._client.table("do_not_call").insert({"phone": phone, "reason": reason}).execute()
        except Exception as e:
            logger.warning(f"Failed to add {phone} to DNC (likely already there): {e}")

    async def _scheduler_batch_loop(self):
        while self._running:
            try:
                now_utc = datetime.now(timezone.utc)
                if self._should_run_batch(now_utc):
                    await self._run_daily_batch()
                    self._last_batch_date = now_utc.date()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(self.SCHEDULER_TICK_SECONDS)

    def _should_run_batch(self, now_utc):
        local = now_utc.astimezone(ZoneInfo(US_TIMEZONE))
        if local.hour != self.BATCH_HOUR_LOCAL:
            return False
        if local.minute >= 5:
            return False
        if self._last_batch_date == now_utc.date():
            return False
        if not is_within_business_hours(now_utc):
            return False
        return True

    async def _run_daily_batch(self):
        leads = pick_leads_for_batch(self._client, limit=self.DAILY_CALL_LIMIT)
        logger.info(f"Daily batch: picked {len(leads)} leads")
        for lead in leads:
            try:
                await self._trigger_call_for_lead(lead)
            except Exception as e:
                logger.error(f"Trigger failed for {lead.get('id')}: {e}")
                continue

    async def _trigger_call_for_lead(self, lead):
        lead_id = lead["id"]
        phone = lead.get("phone")
        if not phone:
            return

        if is_phone_in_dnc(phone, self._client):
            logger.info(f"Skipping {phone}: in DNC")
            return

        call_log = (
            self._client.table("call_logs")
            .insert({
                "lead_id": lead_id,
                "call_type": "cold_call",
                "agent_id": self._agent_id_voice,
                "phone": phone,
                "status": "initiated",
            })
            .execute()
        )
        call_log_id = call_log.data[0]["id"] if call_log.data else None

        self._update_lead(
            lead_id,
            call_status="called",
            last_called_at=datetime.now(timezone.utc).isoformat(),
            call_attempts=lead.get("call_attempts", 0) + 1,
        )

        try:
            result = self._elevenlabs.trigger_outbound_call(
                agent_id=self._agent_id_voice,
                agent_phone_number_id=self._agent_phone_id,
                to_number=phone,
            )
            self._update_call_log_call_data(
                call_log_id,
                conversation_id=result.get("conversation_id"),
                call_sid=result.get("callSid") or result.get("call_sid"),
            )
            self._emitter.emit(
                event_type="setting.call_initiated",
                target_agent=None,
                payload={
                    "lead_id": lead_id,
                    "call_sid": result.get("callSid") or result.get("call_sid", ""),
                    "call_type": "cold_call",
                },
            )
        except ElevenLabsError as e:
            logger.error(f"ElevenLabs trigger failed for {lead_id}: {e}")
            self._update_call_log(call_log_id, status="failed", error=str(e))
            self._update_lead(lead_id, call_status="never_called")
            self._emitter.emit(
                event_type="setting.call_failed",
                target_agent=None,
                payload={"lead_id": lead_id, "reason": str(e)},
            )

    def _update_call_log_call_data(self, call_log_id, conversation_id=None, call_sid=None):
        if call_log_id is None:
            return
        updates = {}
        if conversation_id:
            updates["conversation_id"] = conversation_id
        if call_sid:
            updates["call_sid"] = call_sid
        if updates:
            self._client.table("call_logs").update(updates).eq("id", call_log_id).execute()

    async def _orphan_cleanup_loop(self):
        while self._running:
            try:
                cutoff = (datetime.now(timezone.utc) - timedelta(minutes=self.ORPHAN_THRESHOLD_MINUTES)).isoformat()
                orphans = (
                    self._client.table("call_logs")
                    .select("*")
                    .eq("status", "initiated")
                    .lt("started_at", cutoff)
                    .execute()
                )
                for call in (orphans.data or []):
                    await self._reconcile_orphan(call)
            except Exception as e:
                logger.error(f"Orphan cleanup error: {e}")
            await asyncio.sleep(self.ORPHAN_CHECK_INTERVAL)

    async def _reconcile_orphan(self, call):
        conv_id = call.get("conversation_id")
        if not conv_id:
            self._update_call_log(call["id"], status="failed", error="no conversation_id")
            self._update_lead(call["lead_id"], call_status="never_called")
            return
        try:
            conv = self._elevenlabs.get_conversation(conv_id)
        except ElevenLabsError as e:
            logger.warning(f"Could not fetch orphan conversation {conv_id}: {e}")
            return

        status = conv.get("status", "unknown")
        if status == "done":
            transcript = self._stringify_transcript(conv.get("transcript", []))
            self._emitter.emit(
                event_type="setting.call_completed",
                target_agent="setting",
                payload={
                    "lead_id": call["lead_id"],
                    "conversation_id": conv_id,
                    "transcript": transcript,
                    "duration_seconds": conv.get("duration_seconds", 0),
                },
            )
            self._update_call_log(call["id"], status="completed")
        elif status in ("failed", "no_answer", "busy"):
            self._update_call_log(call["id"], status=status)
            self._update_lead(call["lead_id"], call_status="never_called")

    @staticmethod
    def _stringify_transcript(transcript_data):
        if isinstance(transcript_data, str):
            return transcript_data
        if isinstance(transcript_data, list):
            lines = []
            for turn in transcript_data:
                role = turn.get("role", "speaker")
                msg = turn.get("message", "")
                lines.append(f"{role.title()}: {msg}")
            return "\n".join(lines)
        return ""

    async def start(self):
        self._running = True
        logger.info(f"[{self.agent_id}] Starting Setting Agent (real voice)")
        self._emitter.set_status("idle")
        self._emitter.send_heartbeat()
        self._emitter.emit(
            event_type="system.agent_online",
            target_agent=None,
            payload={"agent_id": self.agent_id},
        )
        await asyncio.gather(
            self._heartbeat_loop(),
            self._poll_events(),
            self._scheduler_batch_loop(),
            self._orphan_cleanup_loop(),
        )


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = SettingAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
