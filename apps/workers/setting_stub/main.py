import asyncio
import logging
import random
import uuid
from dotenv import load_dotenv
from packages.agent_framework import BaseAgent
from packages.agent_framework.supabase_client import create_supabase_client

logger = logging.getLogger(__name__)
ACCEPTANCE_RATE = 0.6


class SettingStubAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_id="setting", **kwargs)

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        if event_type == "scraping.lead_found":
            return await self._handle_lead_found(event)
        elif event_type == "builder.website_ready":
            return await self._handle_website_ready(event)
        else:
            logger.warning(f"Ignoring unknown event type: {event_type}")
            return []

    async def _handle_lead_found(self, event: dict) -> list[dict]:
        lead = event["payload"]["lead"]
        lead_id = event["payload"].get("lead_id", str(uuid.uuid4())[:8])
        lead_name = lead.get("name", "Unknown")

        # Update lead status to 'contacted'
        self._client.table("leads").update({"status": "contacted"}).eq("id", lead_id).execute()

        new_events = []
        new_events.append({"type": "setting.call_started", "target_agent": None, "payload": {"lead_id": lead_id}})
        await asyncio.sleep(random.uniform(1.0, 2.0))

        if random.random() < ACCEPTANCE_RATE:
            logger.info(f"Lead {lead_name} ACCEPTED the proposal")
            # Update lead status to 'accepted'
            self._client.table("leads").update({"status": "accepted"}).eq("id", lead_id).execute()
            new_events.append({"type": "setting.call_accepted", "target_agent": "builder", "payload": {"lead_id": lead_id, "lead": lead}})
        else:
            reason = random.choice(["Non interessato", "Ha già un sito", "Richiamami più tardi", "Numero non raggiungibile"])
            logger.info(f"Lead {lead_name} REJECTED: {reason}")
            # Update lead status to 'rejected'
            self._client.table("leads").update({"status": "rejected"}).eq("id", lead_id).execute()
            new_events.append({"type": "setting.call_rejected", "target_agent": None, "payload": {"lead_id": lead_id, "reason": reason}})
        return new_events

    async def _handle_website_ready(self, event: dict) -> list[dict]:
        lead_id = event["payload"].get("lead_id", "unknown")
        await asyncio.sleep(random.uniform(1.0, 2.0))
        new_events = []
        if random.random() < 0.75:
            amount = random.choice([490, 590, 690, 790, 990])
            logger.info(f"Sale completed for lead {lead_id}: €{amount}")
            new_events.append({"type": "setting.sale_completed", "target_agent": None, "payload": {"lead_id": lead_id, "amount": amount}})
        else:
            logger.info(f"Sale failed for lead {lead_id}")
            new_events.append({"type": "setting.sale_failed", "target_agent": None, "payload": {"lead_id": lead_id, "reason": "Il cliente ha cambiato idea"}})
        return new_events


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = SettingStubAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
