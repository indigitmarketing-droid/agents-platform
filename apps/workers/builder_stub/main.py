import asyncio
import logging
import random
from dotenv import load_dotenv
from packages.agent_framework import BaseAgent
from packages.agent_framework.supabase_client import create_supabase_client

logger = logging.getLogger(__name__)

class BuilderStubAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_id="builder", **kwargs)

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        if event_type != "setting.call_accepted":
            logger.warning(f"Ignoring unknown event type: {event_type}")
            return []

        lead_id = event["payload"].get("lead_id", "unknown")
        lead = event["payload"].get("lead", {})
        lead_name = lead.get("name", "Unknown")
        new_events = []
        new_events.append({"type": "builder.build_started", "target_agent": None, "payload": {"lead_id": lead_id}})
        logger.info(f"Building website for {lead_name}...")
        await asyncio.sleep(random.uniform(3.0, 8.0))
        slug = lead_name.lower().replace(" ", "-").replace("'", "")
        site_url = f"https://{slug}.example.com"
        new_events.append({"type": "builder.website_ready", "target_agent": "setting", "payload": {"lead_id": lead_id, "site_url": site_url}})
        logger.info(f"Website ready for {lead_name}: {site_url}")
        return new_events

async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = BuilderStubAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
