from unittest.mock import MagicMock
from apps.workers.setting_agent.lead_picker import pick_leads_for_batch


def make_mock_supabase(leads_returned: list[dict]):
    """Build a mock Supabase client where the leads query returns given rows."""
    client = MagicMock()
    table = MagicMock()
    builder = MagicMock()
    builder.execute = MagicMock(return_value=MagicMock(data=leads_returned))
    for method in ["select", "eq", "lt", "or_", "order", "limit", "filter"]:
        setattr(builder, method, MagicMock(return_value=builder))
    table.select.return_value = builder
    client.table.return_value = table
    return client


def test_picker_returns_up_to_limit():
    fake_leads = [
        {"id": f"lead-{i}", "phone": f"+1555000{i:04d}", "country_code": "US"}
        for i in range(5)
    ]
    client = make_mock_supabase(fake_leads)
    result = pick_leads_for_batch(client, limit=10)
    assert len(result) == 5


def test_picker_returns_empty_when_no_leads():
    client = make_mock_supabase([])
    result = pick_leads_for_batch(client, limit=10)
    assert result == []


def test_picker_uses_leads_table():
    client = make_mock_supabase([])
    pick_leads_for_batch(client, limit=10)
    client.table.assert_called_with("leads")


def test_picker_respects_limit():
    """The function should pass limit to Supabase query."""
    client = make_mock_supabase([])
    builder = client.table.return_value.select.return_value
    pick_leads_for_batch(client, limit=10)
    builder.limit.assert_called_with(10)
