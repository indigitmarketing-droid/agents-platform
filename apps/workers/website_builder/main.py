"""Real Website Builder Agent. Replaces builder_stub."""
import asyncio
import logging
import os

from dotenv import load_dotenv

from packages.agent_framework import BaseAgent
from packages.agent_framework.supabase_client import create_supabase_client

from apps.workers.website_builder.claude_client import create_anthropic_client
from apps.workers.website_builder.target_analyzer import analyze_target
from apps.workers.website_builder.copy_generator import generate_copy, CopyGenerationError
from apps.workers.website_builder.slug_generator import generate_unique_slug

logger = logging.getLogger(__name__)


class BuilderAgent(BaseAgent):
    """Generates a website for an accepted lead."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="builder", **kwargs)
        try:
            self._claude = create_anthropic_client()
        except KeyError:
            logger.warning("ANTHROPIC_API_KEY not set; agent will fail on Claude calls")
            self._claude = None

    async def handle_event(self, event: dict) -> list[dict]:
        if event.get("type") != "setting.call_accepted":
            logger.debug(f"Ignoring event type: {event.get('type')}")
            return []

        payload = event.get("payload", {})
        lead = payload.get("lead", {})
        lead_id = payload.get("lead_id")
        call_brief = payload.get("call_brief")

        # Accept either `name` or `company_name` (DB column is company_name)
        if not lead.get("name") and lead.get("company_name"):
            lead = {**lead, "name": lead["company_name"]}

        if not lead_id or not lead.get("name"):
            logger.error(f"Invalid call_accepted event payload: {payload}")
            return []

        new_events: list[dict] = []
        new_events.append({
            "type": "builder.build_started",
            "target_agent": None,
            "payload": {"lead_id": lead_id},
        })

        category = lead.get("category", "unknown")
        target = analyze_target(category, call_brief, self._claude)

        try:
            content = generate_copy(target["template_kind"], lead, call_brief, self._claude)
        except CopyGenerationError as e:
            logger.error(f"Copy generation failed for lead {lead_id}: {e}")
            raise

        slug = generate_unique_slug(lead["name"], self._client)
        sites_base = os.environ.get("AGENTS_SITES_BASE_URL", "https://agents-sites.vercel.app")
        site_url = f"{sites_base}/s/{slug}"

        site_insert = self._client.table("sites").insert({
            "lead_id": lead_id,
            "slug": slug,
            "template_kind": target["template_kind"],
            "category": category,
            "colors": target["colors"],
            "content": content,
            "published_url": site_url,
        }).execute()
        site_id = site_insert.data[0]["id"] if site_insert.data else None

        logger.info(f"Site created for {lead['name']}: {site_url} (id={site_id})")

        new_events.append({
            "type": "builder.website_ready",
            "target_agent": "setting",
            "payload": {
                "lead_id": lead_id,
                "site_id": site_id,
                "slug": slug,
                "site_url": site_url,
            },
        })
        return new_events


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = BuilderAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
