import pytest
from unittest.mock import MagicMock
from apps.workers.scraping_worker.main import ScrapingAgent


def make_mock_client():
    """Mock Supabase client with table()/select()/insert() chain."""
    client = MagicMock()
    table = MagicMock()
    # select chain returning empty (no existing leads)
    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.execute = MagicMock(return_value=MagicMock(data=[]))
    table.select.return_value = select_chain
    # insert chain
    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(return_value=MagicMock(data=[{"id": "new-uuid"}]))
    table.insert.return_value = insert_chain
    # update chain
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()
    table.update.return_value = update_chain
    client.table.return_value = table
    return client


def test_save_lead_returns_uuid_when_new():
    client = make_mock_client()
    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "lat": 45.46,
        "lon": 9.18,
        "tags": {
            "name": "Pizzeria Test",
            "phone": "+39 02 12345678",
        },
    }
    target = {
        "id": "target-1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    lead_id = agent._save_lead(osm_element, target)
    assert lead_id == "new-uuid"


def test_save_lead_skips_when_osm_id_exists():
    """If osm_id already in DB, return None and do not insert."""
    client = make_mock_client()
    # Override select for leads to return existing row
    select_chain = client.table().select()
    select_chain.eq.return_value.execute.return_value.data = [{"id": "existing"}]

    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "lat": 45.46,
        "lon": 9.18,
        "tags": {"name": "Existing", "phone": "+39 02 12345678"},
    }
    target = {
        "id": "t1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    result = agent._save_lead(osm_element, target)
    assert result is None


def test_save_lead_skips_when_phone_invalid():
    client = make_mock_client()
    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "tags": {"name": "Test", "phone": "not a phone"},
    }
    target = {
        "id": "t1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    result = agent._save_lead(osm_element, target)
    assert result is None
