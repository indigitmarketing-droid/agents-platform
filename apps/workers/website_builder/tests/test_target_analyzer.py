import json
import pytest
from unittest.mock import MagicMock
from apps.workers.website_builder.target_analyzer import (
    analyze_target,
    TEMPLATE_KIND_MAP,
    DEFAULT_PALETTE,
)


def make_claude_client_returning(palette_dict: dict):
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps(palette_dict))]
    client.messages.create = MagicMock(return_value=response)
    return client


def test_template_kind_maps_restaurant_to_hospitality():
    client = make_claude_client_returning({"primary": "#000000", "accent": "#ffffff", "text": "#000000", "background": "#ffffff"})
    result = analyze_target("restaurant", None, client)
    assert result["template_kind"] == "hospitality"


def test_template_kind_maps_fitness_to_hospitality():
    client = make_claude_client_returning({"primary": "#000000", "accent": "#ffffff", "text": "#000000", "background": "#ffffff"})
    result = analyze_target("fitness_centre", None, client)
    assert result["template_kind"] == "hospitality"


def test_template_kind_maps_hairdresser_to_service():
    client = make_claude_client_returning({"primary": "#000000", "accent": "#ffffff", "text": "#000000", "background": "#ffffff"})
    result = analyze_target("hairdresser", None, client)
    assert result["template_kind"] == "service"


def test_template_kind_maps_unknown_to_generic():
    client = make_claude_client_returning({"primary": "#000000", "accent": "#ffffff", "text": "#000000", "background": "#ffffff"})
    result = analyze_target("unknown_category_xyz", None, client)
    assert result["template_kind"] == "generic"


def test_returns_palette_from_claude():
    palette = {"primary": "#8B4513", "accent": "#D4A574", "text": "#2C2C2C", "background": "#FAF7F2"}
    client = make_claude_client_returning(palette)
    result = analyze_target("restaurant", None, client)
    assert result["colors"] == palette


def test_falls_back_to_default_palette_on_invalid_json():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="not valid json")]
    client.messages.create = MagicMock(return_value=response)
    result = analyze_target("restaurant", None, client)
    assert result["colors"] == DEFAULT_PALETTE


def test_falls_back_to_default_palette_on_missing_keys():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps({"primary": "#000000"}))]
    client.messages.create = MagicMock(return_value=response)
    result = analyze_target("restaurant", None, client)
    assert result["colors"] == DEFAULT_PALETTE


def test_falls_back_to_default_palette_on_invalid_hex():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps({
        "primary": "not-a-hex",
        "accent": "#ffffff",
        "text": "#000000",
        "background": "#ffffff",
    }))]
    client.messages.create = MagicMock(return_value=response)
    result = analyze_target("restaurant", None, client)
    assert result["colors"] == DEFAULT_PALETTE


def test_template_kind_map_contains_all_six_categories():
    expected = {"restaurant", "fitness_centre", "hairdresser", "beauty", "dentist", "photographer"}
    assert expected.issubset(TEMPLATE_KIND_MAP.keys())
