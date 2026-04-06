import pytest
from apps.workers.builder_stub.main import BuilderStubAgent

@pytest.mark.asyncio
async def test_handles_call_accepted():
    from unittest.mock import MagicMock
    agent = BuilderStubAgent(supabase_client=MagicMock())
    event = {"id": "e1", "type": "setting.call_accepted", "payload": {"lead_id": "l1", "lead": {"name": "Test Co", "phone": "+39123"}}, "retry_count": 0}
    result = await agent.handle_event(event)
    types = [e["type"] for e in result]
    assert "builder.build_started" in types
    assert "builder.website_ready" in types

@pytest.mark.asyncio
async def test_website_ready_targets_setting():
    from unittest.mock import MagicMock
    agent = BuilderStubAgent(supabase_client=MagicMock())
    event = {"id": "e1", "type": "setting.call_accepted", "payload": {"lead_id": "l1", "lead": {"name": "Test Co", "phone": "+39123"}}, "retry_count": 0}
    result = await agent.handle_event(event)
    ready_event = next(e for e in result if e["type"] == "builder.website_ready")
    assert ready_event["target_agent"] == "setting"
    assert "site_url" in ready_event["payload"]
    assert "lead_id" in ready_event["payload"]
