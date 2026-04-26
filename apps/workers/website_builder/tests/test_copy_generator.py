import json
import pytest
from unittest.mock import MagicMock
from apps.workers.website_builder.copy_generator import (
    generate_copy,
    CopyGenerationError,
)


SAMPLE_VALID_CONTENT_V2 = {
    "hero": {
        "headline": "La vera pizza napoletana a Milano",
        "subheadline": "Forno a legna dal 1985",
        "cta_text": "Prenota un tavolo",
        "cta_link": "#contact",
        "image_url": "https://images.unsplash.com/photo-1565299624946",
    },
    "problem": {
        "title": "Il problema delle pizzerie a Milano",
        "body": "Trovare una pizza autentica è raro.",
        "bullets": ["Impasti industriali", "Ingredienti scadenti", "Ambienti freddi"],
    },
    "benefits": {
        "title": "Cosa ottieni",
        "items": [
            {"title": "Tradizione napoletana", "description": "Ricetta originale"},
            {"title": "Ingredienti DOP", "description": "Solo materie prime di qualità"},
            {"title": "Esperienza unica", "description": "Atmosfera autentica"},
        ],
    },
    "solution": {
        "title": "Come lavoriamo",
        "body": "Pizza napoletana certificata, forno a legna, lievitazione 24 ore.",
        "cta_text": "Prenota ora",
        "cta_link": "#contact",
    },
    "services": [
        {"title": "Pizza al taglio", "description": "Servizio veloce"},
    ],
    "contacts": {
        "phone": "+39028373248",
        "email": None,
        "address": "Via Roma 12, Milano",
        "opening_hours": "Mar-Dom 12:00-23:00",
    },
}


def make_claude_client_returning(payload):
    client = MagicMock()
    response = MagicMock()
    text = json.dumps(payload) if isinstance(payload, dict) else payload
    response.content = [MagicMock(text=text)]
    client.messages.create = MagicMock(return_value=response)
    return client


def test_generates_pbs_content_for_hospitality():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Pizzeria Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert "hero" in result
    assert "problem" in result
    assert "benefits" in result
    assert "solution" in result
    assert "contacts" in result


def test_problem_section_has_title_body_bullets():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result["problem"]["title"]
    assert result["problem"]["body"]
    assert isinstance(result["problem"]["bullets"], list)


def test_benefits_section_has_items_array():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert isinstance(result["benefits"]["items"], list)
    assert len(result["benefits"]["items"]) >= 1
    assert "title" in result["benefits"]["items"][0]
    assert "description" in result["benefits"]["items"][0]


def test_solution_has_cta_link_to_contact():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result["solution"]["cta_link"] == "#contact"


def test_hero_has_cta_link_to_contact():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result["hero"]["cta_link"] == "#contact"


def test_works_for_service_template():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Studio", "category": "dentist", "city": "Roma", "phone": "+39021234"}
    result = generate_copy("service", lead, None, client)
    assert "problem" in result
    assert "benefits" in result
    assert "solution" in result


def test_works_for_generic_template():
    minimal = {
        "hero": {"headline": "X", "subheadline": "Y", "cta_text": "Contact", "cta_link": "#contact", "image_url": ""},
        "problem": {"title": "P", "body": "B", "bullets": ["a"]},
        "benefits": {"title": "B", "items": [{"title": "x", "description": "y"}]},
        "solution": {"title": "S", "body": "B", "cta_text": "Go", "cta_link": "#contact"},
        "contacts": {"phone": "+39021234"},
    }
    client = make_claude_client_returning(minimal)
    lead = {"name": "X", "category": "unknown", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("generic", lead, None, client)
    assert "problem" in result
    assert "solution" in result


def test_uses_call_brief_in_prompt():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT_V2)
    lead = {"name": "Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    brief = {"custom_requests": "enfatizzare la pizza al taglio", "style_preference": "minimalista"}
    generate_copy("hospitality", lead, brief, client)
    call_args = client.messages.create.call_args
    user_message = call_args.kwargs["messages"][0]["content"]
    assert "pizza al taglio" in user_message.lower()
    assert "minimalista" in user_message.lower()


def test_strips_markdown_code_fences():
    client = make_claude_client_returning(f"```json\n{json.dumps(SAMPLE_VALID_CONTENT_V2)}\n```")
    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result["hero"]["headline"] == SAMPLE_VALID_CONTENT_V2["hero"]["headline"]


def test_retries_on_invalid_json_then_succeeds():
    client = MagicMock()
    bad = MagicMock()
    bad.content = [MagicMock(text="not json")]
    good = MagicMock()
    good.content = [MagicMock(text=json.dumps(SAMPLE_VALID_CONTENT_V2))]
    client.messages.create = MagicMock(side_effect=[bad, good])

    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert "problem" in result
    assert client.messages.create.call_count == 2


def test_raises_after_3_retries():
    client = MagicMock()
    bad = MagicMock()
    bad.content = [MagicMock(text="not json")]
    client.messages.create = MagicMock(return_value=bad)
    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    with pytest.raises(CopyGenerationError):
        generate_copy("hospitality", lead, None, client)
    assert client.messages.create.call_count == 3


def test_validates_missing_problem_key():
    """If Claude omits 'problem', should retry until limit then raise."""
    incomplete = dict(SAMPLE_VALID_CONTENT_V2)
    del incomplete["problem"]
    client = MagicMock()
    bad = MagicMock()
    bad.content = [MagicMock(text=json.dumps(incomplete))]
    client.messages.create = MagicMock(return_value=bad)
    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    with pytest.raises(CopyGenerationError):
        generate_copy("hospitality", lead, None, client)
