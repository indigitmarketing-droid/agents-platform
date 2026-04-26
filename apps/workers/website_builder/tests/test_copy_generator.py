import json
import pytest
from unittest.mock import MagicMock
from apps.workers.website_builder.copy_generator import (
    generate_copy,
    CopyGenerationError,
)


SAMPLE_VALID_CONTENT = {
    "hero": {
        "headline": "La vera pizza napoletana a Milano",
        "subheadline": "Forno a legna dal 1985",
        "cta_text": "Prenota un tavolo",
        "image_url": "https://images.unsplash.com/photo-1565299624946",
    },
    "services": [
        {"title": "Pizza al taglio", "description": "Servizio veloce"},
    ],
    "about": {
        "title": "La nostra storia",
        "body": "Tradizione di famiglia da tre generazioni.",
    },
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


def test_generates_content_with_required_keys_for_hospitality():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT)
    lead = {"name": "Pizzeria Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert "hero" in result
    assert "services" in result
    assert "about" in result
    assert "contacts" in result


def test_generates_content_for_service_template():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT)
    lead = {"name": "Studio Smith", "category": "dentist", "city": "Roma", "phone": "+39021234"}
    result = generate_copy("service", lead, None, client)
    assert "hero" in result
    assert "about" in result


def test_generates_content_for_generic_template():
    client = make_claude_client_returning({
        "hero": {"headline": "Welcome", "subheadline": "", "cta_text": "Contact us", "image_url": ""},
        "about": {"title": "About", "body": "Some text"},
        "contacts": {"phone": "+39021234"},
    })
    lead = {"name": "X", "category": "unknown", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("generic", lead, None, client)
    assert "hero" in result
    assert "about" in result


def test_works_without_call_brief():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT)
    lead = {"name": "Pizzeria Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result == SAMPLE_VALID_CONTENT


def test_uses_call_brief_in_prompt_when_available():
    client = make_claude_client_returning(SAMPLE_VALID_CONTENT)
    lead = {"name": "Pizzeria Mario", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    brief = {"custom_requests": "Enfatizzare la pizza al taglio", "style_preference": "minimalista"}
    generate_copy("hospitality", lead, brief, client)
    call_args = client.messages.create.call_args
    user_message = call_args.kwargs["messages"][0]["content"]
    assert "pizza al taglio" in user_message.lower()
    assert "minimalista" in user_message.lower()


def test_strips_markdown_code_fences_in_response():
    client = make_claude_client_returning(f"```json\n{json.dumps(SAMPLE_VALID_CONTENT)}\n```")
    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert result["hero"]["headline"] == SAMPLE_VALID_CONTENT["hero"]["headline"]


def test_retries_on_invalid_json_then_succeeds():
    client = MagicMock()
    bad_response = MagicMock()
    bad_response.content = [MagicMock(text="not json")]
    good_response = MagicMock()
    good_response.content = [MagicMock(text=json.dumps(SAMPLE_VALID_CONTENT))]
    client.messages.create = MagicMock(side_effect=[bad_response, good_response])

    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    result = generate_copy("hospitality", lead, None, client)
    assert "hero" in result
    assert client.messages.create.call_count == 2


def test_raises_after_3_retries_with_invalid_json():
    client = MagicMock()
    bad_response = MagicMock()
    bad_response.content = [MagicMock(text="not json")]
    client.messages.create = MagicMock(return_value=bad_response)

    lead = {"name": "X", "category": "restaurant", "city": "Milano", "phone": "+39021234"}
    with pytest.raises(CopyGenerationError):
        generate_copy("hospitality", lead, None, client)
    assert client.messages.create.call_count == 3
