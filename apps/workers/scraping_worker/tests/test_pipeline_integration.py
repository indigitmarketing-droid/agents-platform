"""End-to-end pipeline test with mocked Overpass + mocked Supabase."""
import pytest
from unittest.mock import MagicMock
from pytest_httpx import HTTPXMock

from apps.workers.scraping_worker.main import ScrapingAgent


SAMPLE_OVERPASS_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 45.4642,
            "lon": 9.1900,
            "tags": {
                "name": "Pizzeria Da Mario",
                "phone": "+39 02 12345678",
                "amenity": "restaurant",
            },
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 45.4700,
            "lon": 9.1850,
            "tags": {
                "name": "Trattoria Centrale",
                "phone": "02 87654321",
                "amenity": "restaurant",
                "email": "info@trattoria.it",
            },
        },
        {
            "type": "node",
            "id": 1003,
            "lat": 45.4800,
            "lon": 9.1700,
            "tags": {
                "name": "Bad Phone",
                "phone": "not a phone",
                "amenity": "restaurant",
            },
        },
    ]
}


def make_mock_client_with_target(target_dict: dict):
    client = MagicMock()
    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(return_value=MagicMock(data=[{"id": "fake-uuid"}]))
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()

    def table_factory(name):
        t = MagicMock()
        t.insert.return_value = insert_chain
        t.update.return_value = update_chain

        if name == "scraping_targets":
            # select().eq() chain returns target list
            sel = MagicMock()
            sel_eq = MagicMock()
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[target_dict]))
            sel.eq.return_value = sel_eq
            sel.execute = MagicMock(return_value=MagicMock(data=[target_dict]))
            t.select.return_value = sel
        elif name == "leads":
            sel = MagicMock()
            sel_eq = MagicMock()
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
            sel.eq.return_value = sel_eq
            t.select.return_value = sel
        else:
            t.select.return_value = MagicMock()

        return t

    client.table.side_effect = table_factory
    return client


@pytest.mark.asyncio
async def test_run_target_emits_lead_found_for_each_valid_lead(httpx_mock: HTTPXMock):
    target = {
        "id": "target-1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
        "timezone": "Europe/Rome",
        "enabled": True,
        "total_leads_found": 0,
    }
    client = make_mock_client_with_target(target)

    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json=SAMPLE_OVERPASS_RESPONSE,
    )

    agent = ScrapingAgent(supabase_client=client)
    event = {
        "id": "evt-1",
        "type": "scraping.run_target",
        "payload": {"target_id": "target-1"},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)

    lead_events = [e for e in new_events if e["type"] == "scraping.lead_found"]
    assert len(lead_events) == 2  # 3 elements, 1 has invalid phone

    for e in lead_events:
        assert e["target_agent"] == "setting"
        assert "lead_id" in e["payload"]
        assert e["payload"]["lead"]["source"] == "openstreetmap"


@pytest.mark.asyncio
async def test_trigger_all_emits_run_target_per_enabled(httpx_mock: HTTPXMock):
    target = {
        "id": "target-1",
        "timezone": "Europe/Rome",
        "enabled": True,
    }
    client = make_mock_client_with_target(target)

    agent = ScrapingAgent(supabase_client=client)
    event = {
        "id": "evt-1",
        "type": "scraping.trigger",
        "payload": {},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)
    run_events = [e for e in new_events if e["type"] == "scraping.run_target"]
    assert len(run_events) >= 1
    assert run_events[0]["target_agent"] == "scraping"
    assert run_events[0]["payload"]["target_id"] == "target-1"
