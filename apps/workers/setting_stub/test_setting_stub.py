import pytest
from apps.workers.setting_stub.main import SettingStubAgent

@pytest.mark.asyncio
async def test_handles_lead_found_accept():
    from unittest.mock import MagicMock
    agent = SettingStubAgent(supabase_client=MagicMock())
    import random
    random.seed(42)
    event = {"id": "e1", "type": "scraping.lead_found", "payload": {"lead": {"name": "Test Co", "phone": "+39123", "source": "test"}}, "retry_count": 0}
    result = await agent.handle_event(event)
    types = [e["type"] for e in result]
    assert "setting.call_started" in types
    assert ("setting.call_accepted" in types or "setting.call_rejected" in types)

@pytest.mark.asyncio
async def test_handles_website_ready():
    from unittest.mock import MagicMock
    agent = SettingStubAgent(supabase_client=MagicMock())
    event = {"id": "e2", "type": "builder.website_ready", "payload": {"lead_id": "l1", "site_url": "https://example.com"}, "retry_count": 0}
    result = await agent.handle_event(event)
    types = [e["type"] for e in result]
    assert ("setting.sale_completed" in types or "setting.sale_failed" in types)

@pytest.mark.asyncio
async def test_accepted_targets_builder():
    from unittest.mock import MagicMock
    import random
    random.seed(1)
    agent = SettingStubAgent(supabase_client=MagicMock())
    event = {"id": "e1", "type": "scraping.lead_found", "payload": {"lead": {"name": "Test", "phone": "+39123", "source": "test"}}, "retry_count": 0}
    result = await agent.handle_event(event)
    accepted = [e for e in result if e["type"] == "setting.call_accepted"]
    if accepted:
        assert accepted[0]["target_agent"] == "builder"
