import pytest
from apps.workers.scraping_stub.main import ScrapingStubAgent

@pytest.mark.asyncio
async def test_handles_trigger_event():
    from unittest.mock import MagicMock
    agent = ScrapingStubAgent(supabase_client=MagicMock())
    event = {"id": "e1", "type": "scraping.trigger", "payload": {"batch_size": 3}, "retry_count": 0}
    result = await agent.handle_event(event)
    assert len(result) >= 2
    lead_events = [e for e in result if e["type"] == "scraping.lead_found"]
    batch_events = [e for e in result if e["type"] == "scraping.batch_completed"]
    assert len(lead_events) >= 1
    assert len(batch_events) == 1
    assert batch_events[0]["payload"]["total_found"] == len(lead_events)

@pytest.mark.asyncio
async def test_lead_found_has_required_fields():
    from unittest.mock import MagicMock
    agent = ScrapingStubAgent(supabase_client=MagicMock())
    event = {"id": "e1", "type": "scraping.trigger", "payload": {}, "retry_count": 0}
    result = await agent.handle_event(event)
    lead_event = next(e for e in result if e["type"] == "scraping.lead_found")
    lead = lead_event["payload"]["lead"]
    assert "name" in lead
    assert "phone" in lead
    assert "source" in lead
    assert lead_event["target_agent"] == "setting"
