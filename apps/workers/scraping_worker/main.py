"""Real scraping agent using OpenStreetMap via Overpass API."""
import asyncio
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from packages.agent_framework import BaseAgent, FatalError
from packages.agent_framework.supabase_client import create_supabase_client

from apps.workers.scraping_worker.overpass_client import (
    OverpassClient,
    OverpassError,
)
from apps.workers.scraping_worker.phone_normalizer import normalize_phone
from apps.workers.scraping_worker.query_builder import build_no_website_query
from apps.workers.scraping_worker.scheduler import Target, TimezoneScheduler

logger = logging.getLogger(__name__)


class ScrapingAgent(BaseAgent):
    """Real scraping agent. Replaces ScrapingStubAgent."""

    SCHEDULER_INTERVAL = 60

    def __init__(self, **kwargs):
        super().__init__(agent_id="scraping", **kwargs)
        self._overpass = OverpassClient()
        self._scheduler = TimezoneScheduler()

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        payload = event.get("payload", {})

        if event_type == "scraping.trigger":
            return await self._handle_trigger_all()

        if event_type == "scraping.run_target":
            target_id = payload.get("target_id")
            if not target_id:
                raise FatalError("scraping.run_target missing target_id")
            return await self._handle_run_target(target_id)

        logger.warning(f"Ignoring unknown event type: {event_type}")
        return []

    async def _handle_trigger_all(self) -> list[dict]:
        targets = self._load_enabled_targets()
        return [
            {
                "type": "scraping.run_target",
                "target_agent": "scraping",
                "payload": {"target_id": t["id"]},
            }
            for t in targets
        ]

    async def _handle_run_target(self, target_id: str) -> list[dict]:
        target = self._load_target(target_id)
        if target is None:
            raise FatalError(f"Target {target_id} not found")

        run_id = self._create_run(target_id)

        try:
            query = build_no_website_query(
                target["category_type"],
                target["category"],
                target["city"],
            )
            elements = await self._overpass.query(query)
            logger.info(f"Overpass returned {len(elements)} elements for {target['city']}/{target['category']}")
        except OverpassError as e:
            self._fail_run(run_id, str(e))
            raise FatalError(f"Overpass query failed: {e}")

        new_events = []
        leads_new = 0
        for element in elements:
            lead_id = self._save_lead(element, target)
            if lead_id is None:
                continue
            leads_new += 1
            tags = element.get("tags", {})
            new_events.append({
                "type": "scraping.lead_found",
                "target_agent": "setting",
                "payload": {
                    "lead_id": lead_id,
                    "lead": {
                        "name": tags.get("name", "Unknown"),
                        "phone": normalize_phone(tags.get("phone", ""), target["country_code"]),
                        "email": tags.get("email"),
                        "source": "openstreetmap",
                    },
                },
            })

        self._complete_run(run_id, leads_found=len(elements), leads_new=leads_new)
        self._update_target_last_run(target_id, leads_new)
        return new_events

    def _load_enabled_targets(self) -> list[dict]:
        result = (
            self._client.table("scraping_targets")
            .select("*")
            .eq("enabled", True)
            .execute()
        )
        return result.data or []

    def _load_target(self, target_id: str) -> dict | None:
        result = (
            self._client.table("scraping_targets")
            .select("*")
            .eq("id", target_id)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    def _create_run(self, target_id: str) -> str:
        result = (
            self._client.table("scraping_runs")
            .insert({"target_id": target_id, "status": "running"})
            .execute()
        )
        return result.data[0]["id"] if result.data else ""

    def _complete_run(self, run_id: str, leads_found: int, leads_new: int) -> None:
        (
            self._client.table("scraping_runs")
            .update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "leads_found": leads_found,
                "leads_new": leads_new,
            })
            .eq("id", run_id)
            .execute()
        )

    def _fail_run(self, run_id: str, error: str) -> None:
        (
            self._client.table("scraping_runs")
            .update({
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": error,
            })
            .eq("id", run_id)
            .execute()
        )

    def _update_target_last_run(self, target_id: str, leads_new: int) -> None:
        target = self._load_target(target_id)
        if target is None:
            return
        new_total = (target.get("total_leads_found") or 0) + leads_new
        (
            self._client.table("scraping_targets")
            .update({
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "total_leads_found": new_total,
            })
            .eq("id", target_id)
            .execute()
        )

    def _save_lead(self, element: dict, target: dict) -> str | None:
        osm_id = f"node/{element.get('id')}"
        tags = element.get("tags", {})
        raw_phone = tags.get("phone", "")
        phone = normalize_phone(raw_phone, target["country_code"])
        if phone is None:
            logger.debug(f"Skip {osm_id}: invalid phone '{raw_phone}'")
            return None

        existing = (
            self._client.table("leads")
            .select("id")
            .eq("osm_id", osm_id)
            .execute()
        )
        if existing.data:
            logger.debug(f"Skip {osm_id}: already in DB")
            return None

        row = {
            "company_name": tags.get("name", "Unknown"),
            "phone": phone,
            "email": tags.get("email"),
            "has_website": False,
            "status": "new",
            "source": "openstreetmap",
            "osm_id": osm_id,
            "category": target["category"],
            "city": target["city"],
            "country_code": target["country_code"],
            "latitude": element.get("lat"),
            "longitude": element.get("lon"),
        }
        result = self._client.table("leads").insert(row).execute()
        if result.data:
            return result.data[0]["id"]
        return None

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                rows = self._load_enabled_targets()
                targets = [
                    Target(
                        id=r["id"],
                        timezone=r["timezone"],
                        enabled=r["enabled"],
                        last_run_at=datetime.fromisoformat(r["last_run_at"])
                            if r.get("last_run_at") else None,
                    )
                    for r in rows
                ]
                now_utc = datetime.now(timezone.utc)
                due = self._scheduler.get_targets_to_run(targets, now_utc)
                for t in due:
                    logger.info(f"Scheduler: emitting run_target for {t.id}")
                    self._emitter.emit(
                        event_type="scraping.run_target",
                        target_agent="scraping",
                        payload={"target_id": t.id},
                    )
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(self.SCHEDULER_INTERVAL)

    async def start(self) -> None:
        self._running = True
        logger.info(f"[{self.agent_id}] Starting agent (real OSM)")
        self._emitter.set_status("idle")
        self._emitter.send_heartbeat()
        self._emitter.emit("system.agent_online", {"agent_id": self.agent_id})
        await asyncio.gather(
            self._heartbeat_loop(),
            self._poll_events(),
            self._scheduler_loop(),
        )


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = ScrapingAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
