"""
Integration test: verifies the full event pipeline with stub agents.
Simulates the complete flow without a real Supabase instance.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from apps.workers.scraping_stub.main import ScrapingStubAgent
from apps.workers.setting_stub.main import SettingStubAgent
from apps.workers.builder_stub.main import BuilderStubAgent


@pytest.mark.asyncio
async def test_full_pipeline_stub_flow():
    """
    Simulate the full pipeline without Supabase:
    scraping.trigger → lead_found → call_accepted → build → website_ready → sale
    """
    mock_client = MagicMock()

    scraping = ScrapingStubAgent(supabase_client=mock_client)
    setting = SettingStubAgent(supabase_client=mock_client)
    builder = BuilderStubAgent(supabase_client=mock_client)

    # Step 1: Trigger scraping
    trigger_event = {
        "id": "t1",
        "type": "scraping.trigger",
        "payload": {"batch_size": 2},
        "retry_count": 0,
    }
    scraping_results = await scraping.handle_event(trigger_event)
    leads = [e for e in scraping_results if e["type"] == "scraping.lead_found"]
    assert len(leads) >= 1, "Scraping should find at least 1 lead"

    # Step 2: Setting handles first lead
    lead_event = {
        "id": "l1",
        "type": leads[0]["type"],
        "payload": leads[0]["payload"],
        "retry_count": 0,
    }
    setting_results = await setting.handle_event(lead_event)
    call_events = [
        e for e in setting_results
        if e["type"] in ("setting.call_accepted", "setting.call_rejected")
    ]
    assert len(call_events) == 1, "Setting should produce exactly one call result"

    # Step 3: If accepted, builder handles it
    accepted = [e for e in setting_results if e["type"] == "setting.call_accepted"]
    if accepted:
        build_event = {
            "id": "b1",
            "type": accepted[0]["type"],
            "payload": accepted[0]["payload"],
            "retry_count": 0,
        }
        builder_results = await builder.handle_event(build_event)
        ready = [e for e in builder_results if e["type"] == "builder.website_ready"]
        assert len(ready) == 1, "Builder should produce exactly one website_ready"
        assert ready[0]["target_agent"] == "setting"

        # Step 4: Setting handles website_ready
        sale_event = {
            "id": "s1",
            "type": ready[0]["type"],
            "payload": ready[0]["payload"],
            "retry_count": 0,
        }
        sale_results = await setting.handle_event(sale_event)
        sale_types = [e["type"] for e in sale_results]
        assert (
            "setting.sale_completed" in sale_types
            or "setting.sale_failed" in sale_types
        ), "Setting should produce a sale result"
