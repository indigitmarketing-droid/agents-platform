import pytest
from unittest.mock import MagicMock
from packages.agent_framework.event_emitter import EventEmitter

@pytest.fixture
def mock_supabase():
    client = MagicMock()
    table = MagicMock()
    insert = MagicMock()
    insert.execute = MagicMock(return_value=MagicMock(data=[{"id": "test-uuid"}]))
    table.insert.return_value = insert
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()
    table.update.return_value = update_chain
    client.table.return_value = table
    return client

def test_emit_event(mock_supabase):
    emitter = EventEmitter(client=mock_supabase, agent_id="scraping")
    result = emitter.emit(
        event_type="scraping.lead_found",
        payload={"lead": {"name": "Test Co", "phone": "+39123", "source": "test"}},
        target_agent="setting",
    )
    mock_supabase.table.assert_called_with("events")
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["type"] == "scraping.lead_found"
    assert call_args["source_agent"] == "scraping"
    assert call_args["target_agent"] == "setting"
    assert call_args["status"] == "pending"

def test_emit_broadcast_event(mock_supabase):
    emitter = EventEmitter(client=mock_supabase, agent_id="scraping")
    emitter.emit(
        event_type="scraping.batch_completed",
        payload={"total_found": 5, "batch_id": "b1"},
    )
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["target_agent"] is None

def test_heartbeat(mock_supabase):
    emitter = EventEmitter(client=mock_supabase, agent_id="scraping")
    emitter.send_heartbeat()
    mock_supabase.table.assert_called_with("agents")
