# packages/events_schema/test_schemas.py
import json
import os
import pytest
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent / "schemas"

def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / f"{name}.json") as f:
        return json.load(f)

def test_scraping_schema_loads():
    schema = load_schema("scraping")
    assert "definitions" in schema
    assert "scraping.trigger" in schema["definitions"]
    assert "scraping.lead_found" in schema["definitions"]
    assert "scraping.batch_completed" in schema["definitions"]

def test_setting_schema_loads():
    schema = load_schema("setting")
    assert "definitions" in schema
    assert "setting.call_accepted" in schema["definitions"]
    assert "setting.call_rejected" in schema["definitions"]
    assert "setting.sale_completed" in schema["definitions"]

def test_builder_schema_loads():
    schema = load_schema("builder")
    assert "definitions" in schema
    assert "builder.build_started" in schema["definitions"]
    assert "builder.website_ready" in schema["definitions"]

def test_system_schema_loads():
    schema = load_schema("system")
    assert "definitions" in schema
    assert "system.agent_online" in schema["definitions"]
    assert "system.error" in schema["definitions"]

def test_lead_found_payload_has_required_fields():
    schema = load_schema("scraping")
    lead_found = schema["definitions"]["scraping.lead_found"]
    lead_props = lead_found["properties"]["lead"]["properties"]
    assert "name" in lead_props
    assert "phone" in lead_props
    assert "source" in lead_props
