"""Generate website content (JSON) using Claude — v2 PBS schema."""
import json
import logging

logger = logging.getLogger(__name__)


class CopyGenerationError(Exception):
    """Claude failed to generate valid content after retries."""


# All templates use the v2 PBS structure
_REQUIRED_KEYS_V2: list[str] = ["hero", "problem", "benefits", "solution", "contacts"]


def generate_copy(
    template_kind: str,
    lead: dict,
    call_brief: dict | None,
    claude_client,
    max_retries: int = 3,
) -> dict:
    """Ask Claude to generate website content JSON in v2 PBS format."""
    prompt = _build_prompt(template_kind, lead, call_brief)

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            content = _parse_json(text)
            _validate_content(content, _REQUIRED_KEYS_V2)
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

    schema = _schema_v2()

    return (
        f"Sei un copywriter italiano per piccole attività locali. Devi generare contenuti "
        f"di un sito web ULTRA PREMIUM seguendo il framework Problema → Beneficio → Soluzione.\n\n"
        f"Business:\n"
        f"- Nome: {name}\n"
        f"- Categoria: {category}\n"
        f"- Città: {city}"
        f"{brief_section}\n\n"
        f"Struttura del copy:\n"
        f"1. PROBLEMA: identifica il pain point principale del cliente target. "
        f"Cosa frustra chi cerca {category} a {city}? Quale problema concreto ha?\n"
        f"2. BENEFICI: 3 risultati concreti che il cliente ottiene scegliendo {name}.\n"
        f"3. SOLUZIONE: come {name} risolve il problema in modo unico.\n\n"
        f"Tono: professionale, sicuro, conversion-focused. Niente 'Chi siamo' generico. "
        f"Ogni CTA (cta_link) deve essere '#contact' (link al form).\n\n"
        f"Output ESCLUSIVAMENTE JSON valido, senza markdown, senza prosa, "
        f"matching esatto questa struttura:\n{schema}\n\n"
        f"Usa Unsplash per image_url (https://images.unsplash.com/...). "
        f"Tutto in italiano."
    )


def _schema_v2() -> str:
    return (
        '{\n'
        '  "hero": {\n'
        '    "headline": "promessa di valore in 1 riga",\n'
        '    "subheadline": "chiarimento + per chi è",\n'
        '    "cta_text": "azione (es. Richiedi un preventivo)",\n'
        '    "cta_link": "#contact",\n'
        '    "image_url": "https://images.unsplash.com/..."\n'
        '  },\n'
        '  "problem": {\n'
        '    "title": "Il problema (es. La sfida che risolviamo)",\n'
        '    "body": "descrizione narrativa del pain point",\n'
        '    "bullets": ["pain1", "pain2", "pain3"]\n'
        '  },\n'
        '  "benefits": {\n'
        '    "title": "Cosa ottieni",\n'
        '    "items": [\n'
        '      {"title": "Beneficio 1", "description": "dettaglio"},\n'
        '      {"title": "Beneficio 2", "description": "dettaglio"},\n'
        '      {"title": "Beneficio 3", "description": "dettaglio"}\n'
        '    ]\n'
        '  },\n'
        '  "solution": {\n'
        '    "title": "Come funziona / Come lavoriamo",\n'
        '    "body": "narrativa: chi siete, cosa offrite concretamente",\n'
        '    "cta_text": "Inizia ora",\n'
        '    "cta_link": "#contact"\n'
        '  },\n'
        '  "services": [\n'
        '    {"title": "...", "description": "..."}\n'
        '  ],\n'
        '  "contacts": {\n'
        '    "phone": "...",\n'
        '    "email": "..." or null,\n'
        '    "address": "..." or null,\n'
        '    "opening_hours": "..." or null\n'
        '  }\n'
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
