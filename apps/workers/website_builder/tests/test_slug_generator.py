import pytest
from unittest.mock import MagicMock
from apps.workers.website_builder.slug_generator import generate_unique_slug


def make_client_with_existing(existing_slugs: list[str]):
    """Mock Supabase client where given slugs already exist in `sites` table."""
    client = MagicMock()
    table = MagicMock()
    select = MagicMock()
    select.eq.return_value = select

    def execute_for_slug(slug_being_checked: str):
        return MagicMock(data=[{"id": "existing"}] if slug_being_checked in existing_slugs else [])

    def eq_capture(_field, value):
        result = MagicMock()
        result.execute = MagicMock(return_value=execute_for_slug(value))
        return result

    select.eq = MagicMock(side_effect=eq_capture)
    table.select.return_value = select
    client.table.return_value = table
    return client


def test_generate_basic_slug_from_company_name():
    client = make_client_with_existing([])
    assert generate_unique_slug("Pizzeria Da Mario", client) == "pizzeria-da-mario"


def test_generate_slug_strips_special_chars():
    client = make_client_with_existing([])
    assert generate_unique_slug("Caffè & Co.", client) == "caffe-and-co"


def test_generate_slug_lowercase():
    client = make_client_with_existing([])
    assert generate_unique_slug("RISTORANTE LUIGI", client) == "ristorante-luigi"


def test_generate_slug_appends_2_when_collision():
    client = make_client_with_existing(["pizzeria-mario"])
    assert generate_unique_slug("Pizzeria Mario", client) == "pizzeria-mario-2"


def test_generate_slug_appends_3_when_two_collisions():
    client = make_client_with_existing(["pizzeria-mario", "pizzeria-mario-2"])
    assert generate_unique_slug("Pizzeria Mario", client) == "pizzeria-mario-3"


def test_generate_slug_handles_apostrophes():
    client = make_client_with_existing([])
    assert generate_unique_slug("L'Osteria Roma", client) == "losteria-roma"
