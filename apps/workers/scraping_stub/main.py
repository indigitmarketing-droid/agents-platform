import asyncio
import logging
import random
import uuid
from dotenv import load_dotenv
from packages.agent_framework import BaseAgent
from packages.agent_framework.supabase_client import create_supabase_client

logger = logging.getLogger(__name__)

FAKE_COMPANIES = [
    ("Pizzeria Da Mario", "+39 06 1234567", "mario@email.com"),
    ("Idraulica Rossi", "+39 02 9876543", "rossi@email.com"),
    ("Bar Sport", "+39 055 1112233", None),
    ("Officina Verdi", "+39 011 4445566", "verdi@email.com"),
    ("Forno Bianchi", "+39 081 7778899", None),
    ("Parrucchiere Stella", "+39 06 2223344", "stella@email.com"),
    ("Autolavaggio Flash", "+39 02 5556677", None),
    ("Ristorante La Pergola", "+39 055 8889900", "pergola@email.com"),
    ("Ferramenta Conti", "+39 011 1234567", None),
    ("Gelateria Dolce Vita", "+39 081 9876543", "dolcevita@email.com"),
]

class ScrapingStubAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_id="scraping", **kwargs)

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        if event_type != "scraping.trigger":
            logger.warning(f"Ignoring unknown event type: {event_type}")
            return []

        batch_size = event.get("payload", {}).get("batch_size", 5)
        batch_size = min(batch_size, len(FAKE_COMPANIES))
        batch_id = str(uuid.uuid4())[:8]
        logger.info(f"Starting scraping batch {batch_id}, size={batch_size}")

        new_events = []
        selected = random.sample(FAKE_COMPANIES, batch_size)

        for name, phone, email in selected:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            new_events.append({
                "type": "scraping.lead_found",
                "target_agent": "setting",
                "payload": {"lead": {"name": name, "phone": phone, "email": email, "source": "stub_scraper"}},
            })
            logger.info(f"Found lead: {name}")

        new_events.append({
            "type": "scraping.batch_completed",
            "target_agent": None,
            "payload": {"total_found": len(selected), "batch_id": batch_id},
        })
        return new_events

async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = ScrapingStubAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
