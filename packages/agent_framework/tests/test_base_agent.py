import pytest
from unittest.mock import AsyncMock, MagicMock
from packages.agent_framework.base_agent import BaseAgent

class StubAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_id="test_agent", **kwargs)
        self.handled_events = []

    async def handle_event(self, event: dict) -> list[dict]:
        self.handled_events.append(event)
        return [{"type": "test.output", "payload": {"result": "ok"}, "target_agent": None}]

def test_agent_has_id():
    agent = StubAgent(supabase_client=MagicMock())
    assert agent.agent_id == "test_agent"

@pytest.mark.asyncio
async def test_handle_event_returns_new_events():
    agent = StubAgent(supabase_client=MagicMock())
    input_event = {"id": "e1", "type": "test.input", "payload": {}}
    result = await agent.handle_event(input_event)
    assert len(result) == 1
    assert result[0]["type"] == "test.output"

@pytest.mark.asyncio
async def test_process_event_emits_results():
    mock_client = MagicMock()
    table = MagicMock()
    insert = MagicMock()
    insert.execute = AsyncMock(return_value=MagicMock(data=[{"id": "new-uuid"}]))
    table.insert.return_value = insert
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = AsyncMock()
    table.update.return_value = update_chain
    mock_client.table.return_value = table

    agent = StubAgent(supabase_client=mock_client)
    event = {"id": "e1", "type": "test.input", "payload": {}, "retry_count": 0}
    await agent.process_event(event)
    assert len(agent.handled_events) == 1
