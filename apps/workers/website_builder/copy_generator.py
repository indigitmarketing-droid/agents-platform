"""Generate website content (JSON) using Claude."""
import json
import logging

logger = logging.getLogger(__name__)


class CopyGenerationError(Exception):
    """Claude failed to generate valid content after retries."""


_TEMPLATE_REQUIRED_KEYS: dict[str, list[str]] = {
    "hospitality": ["hero", "services", "about", "contacts"],
    "service": ["hero", "about", "services", "contacts"],
    "generic": ["hero", "about", "contacts"],
}


def generate_copy(
    template_kind: str,
    lead: dict,
    call_brief: dict | None,
    claude_client,
    max_retries: int = 3,
) -> dict:
    """Ask Claude to generate website content JSON. Retries on JSON parse error."""
    prompt = _build_prompt(template_kind, lead, call_brief)
    required_keys = _TEMPLATE_REQUIRED_KEYS.get(template_kind, ["hero", "about", "contacts"])

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            content = _parse_json(text)
            _validate_content(content, required_keys)
            return content
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Copy attempt {attempt + 1}/{max_retries} failed: {e}")
            last_error = e

    raise CopyGenerationError(
        f"Failed to generate valid copy after {max_retries} attempts: {last_error}"
    )


def _build_prompt(template_kind: str, lead: dict, call_brief: dict | None) -> str:
    name = lead.get("name", "Unknown")
    category = lead.get("category", "business")
    city = lead.get("city", "")

    brief_section = ""
    if call_brief:
        parts = []
        if call_brief.get("custom_requests"):
            parts.append(f"Customer requests: {call_brief['custom_requests']}")
        if call_brief.get("services"):
            services = ", ".join(call_brief["services"])
            parts.append(f"Services to highlight: {services}")
        if call_brief.get("style_preference"):
            parts.append(f"Style preference: {call_brief['style_preference']}")
        if call_brief.get("target_audience"):
            parts.append(f"Target audience: {call_brief['target_audience']}")
        if call_brief.get("opening_hours"):
            parts.append(f"Opening hours: {call_brief['opening_hours']}")
        if parts:
            brief_section = "\n\nBrief from sales call:\n" + "\n".join(f"- {p}" for p in parts)

    schema_description = _schema_description_for(template_kind)

    return (
        f"You are an Italian copywriter for small local businesses. Write website content "
        f"in Italian for:\n"
        f"- Business name: {name}\n"
        f"- Category: {category}\n"
        f"- City: {city}"
        f"{brief_section}\n\n"
        f"Output ONLY valid JSON matching this schema (no markdown, no prose):\n"
        f"{schema_description}\n"
        f"Use Unsplash CDN for image_url (https://images.unsplash.com/...). "
        f"Tone: professional, conversion-oriented."
    )


def _schema_description_for(template_kind: str) -> str:
    if template_kind == "hospitality":
        return (
            '{\n'
            '  "hero": {"headline": str, "subheadline": str, "cta_text": str, "image_url": str},\n'
            '  "services": [{"title": str, "description": str}],\n'
            '  "about": {"title": str, "body": str},\n'
            '  "contacts": {"phone": str, "email": str|null, "address": str|null, "opening_hours": str|null}\n'
            '}'
        )
    if template_kind == "service":
        return (
            '{\n'
            '  "hero": {"headline": str, "subheadline": str, "cta_text": str, "image_url": str},\n'
            '  "about": {"title": str, "body": str},\n'
            '  "services": [{"title": str, "description": str, "price": str|null}],\n'
            '  "contacts": {"phone": str, "email": str|null, "address": str|null, "opening_hours": str|null}\n'
            '}'
        )
    return (
        '{\n'
        '  "hero": {"headline": str, "subheadline": str, "cta_text": str, "image_url": str},\n'
        '  "about": {"title": str, "body": str},\n'
        '  "contacts": {"phone": str, "email": str|null, "address": str|null}\n'
        '}'
    )


def _parse_json(text: str) -> dict:
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def _validate_content(content: dict, required_keys: list[str]) -> None:
    if not isinstance(content, dict):
        raise ValueError(f"Expected dict, got {type(content).__name__}")
    for key in required_keys:
        if key not in content:
            raise ValueError(f"Missing required key: {key}")
