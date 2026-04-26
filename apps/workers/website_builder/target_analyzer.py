"""Analyze target: pick template_kind from category mapping; ask Claude for color palette."""
import json
import logging
import re

logger = logging.getLogger(__name__)


TEMPLATE_KIND_MAP: dict[str, str] = {
    "restaurant": "hospitality",
    "fitness_centre": "hospitality",
    "hairdresser": "service",
    "beauty": "service",
    "dentist": "service",
    "photographer": "service",
}


DEFAULT_PALETTE: dict[str, str] = {
    "primary": "#5B4FCF",
    "accent": "#A78BFA",
    "text": "#1F2937",
    "background": "#F9FAFB",
}


_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_REQUIRED_KEYS = ("primary", "accent", "text", "background")


def analyze_target(category: str, call_brief: dict | None, claude_client) -> dict:
    """
    Decide the template kind and color palette for a site.

    Returns:
        {"template_kind": "hospitality"|"service"|"generic", "colors": {...}}
    """
    template_kind = TEMPLATE_KIND_MAP.get(category, "generic")
    colors = _generate_palette(category, call_brief, claude_client)
    return {"template_kind": template_kind, "colors": colors}


def _generate_palette(category: str, call_brief: dict | None, claude_client) -> dict:
    style_hint = ""
    if call_brief and call_brief.get("style_preference"):
        style_hint = f" Style preference: {call_brief['style_preference']}."

    prompt = (
        f"You are a brand designer. Suggest a 4-color palette for a small "
        f"local business website in the category '{category}'.{style_hint} "
        f"Return ONLY valid JSON with exactly these keys: primary, accent, "
        f"text, background. Each value must be a 7-character hex color "
        f"(e.g., \"#8B4513\"). No prose, no markdown."
    )

    try:
        response = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        palette = json.loads(text)
    except (json.JSONDecodeError, AttributeError, KeyError, IndexError) as e:
        logger.warning(f"Failed to parse Claude palette for {category}: {e}; using default")
        return DEFAULT_PALETTE

    if not _is_valid_palette(palette):
        logger.warning(f"Invalid palette from Claude for {category}: {palette}; using default")
        return DEFAULT_PALETTE

    return {key: palette[key] for key in _REQUIRED_KEYS}


def _is_valid_palette(palette: dict) -> bool:
    if not isinstance(palette, dict):
        return False
    for key in _REQUIRED_KEYS:
        if key not in palette:
            return False
        if not isinstance(palette[key], str):
            return False
        if not _HEX_RE.match(palette[key]):
            return False
    return True
