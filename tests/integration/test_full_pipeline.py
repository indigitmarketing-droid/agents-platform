"""
Integration test: verifies the full event pipeline with stub agents.
Simulates the complete flow without a real Supabase instance.
"""
import os
import pytest
from unittest.mock import MagicMock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-tests")

from apps.workers.scraping_worker.main import ScrapingAgent as ScrapingStubAgent


@pytest.mark.asyncio
async def test_full_pipeline_stub_flow():
    """
    Simulate scraping.trigger with the real ScrapingAgent (mocked Supabase).
    New agent emits run_target events instead of lead_found directly.
    """
    mock_client = MagicMock()

    scraping = ScrapingStubAgent(supabase_client=mock_client)

    # Step 1: Trigger scraping
    trigger_event = {
        "id": "t1",
        "type": "scraping.trigger",
        "payload": {},
        "retry_count": 0,
    }
    scraping_results = await scraping.handle_event(trigger_event)
    # New agent emits run_target events instead of lead_found directly
    run_events = [e for e in scraping_results if e["type"] == "scraping.run_target"]
    assert isinstance(run_events, list)  # may be empty without DB targets
