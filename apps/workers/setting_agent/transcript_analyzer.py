"""Use Claude to extract outcome + call_brief from a call transcript."""
import json
import logging

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Claude failed to produce valid analysis after retries."""


def analyze_transcript(
    transcript: str,
    lead: dict,
    claude_client,
    max_retries: int = 3,
) -> dict:
    """
    Extract outcome + opt_out + call_brief from a sales call transcript.

    Returns:
        {"outcome": "accepted"|"rejected"|"unclear", "opt_out": bool, "call_brief": dict|None}
    """
    prompt = _build_prompt(transcript, lead)
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            data = _parse_json(text)
            _validate(data)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Transcript analyze attempt {attempt + 1} failed: {e}")
            last_error = e

    raise AnalysisError(f"Failed to analyze transcript after {max_retries} attempts: {last_error}")


def _build_prompt(transcript: str, lead: dict) -> str:
    name = lead.get("name", "Unknown")
    category = lead.get("category", "business")
    city = lead.get("city", "")

    return (
        f"You are analyzing a sales call transcript (English) for a free website-rebuild service.\n"
        f"Lead context: {name}, {category}, {city}.\n\n"
        f"Extract from the transcript:\n"
        f"1. outcome: \"accepted\" | \"rejected\" | \"unclear\"\n"
        f"   - accepted: lead agreed to receive a free website demo\n"
        f"   - rejected: lead clearly declined\n"
        f"   - unclear: ambiguous, voicemail, partial conversation, hung up early\n"
        f"2. opt_out: true if lead explicitly said \"do not call again\" or similar\n"
        f"3. call_brief: ONLY if outcome is \"accepted\", otherwise null. Object with:\n"
        f"   - custom_requests (string)\n"
        f"   - services (array of strings)\n"
        f"   - style_preference (string)\n"
        f"   - target_audience (string)\n"
        f"   - opening_hours (string)\n\n"
        f"Output ONLY valid JSON, no prose, no markdown.\n\n"
        f"Transcript:\n{transcript}"
    )


def _parse_json(text: str) -> dict:
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def _validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}")
    if "outcome" not in data:
        raise ValueError("Missing 'outcome' key")
    if data["outcome"] not in ("accepted", "rejected", "unclear"):
        raise ValueError(f"Invalid outcome: {data['outcome']}")
    if "opt_out" not in data:
        raise ValueError("Missing 'opt_out' key")
    if "call_brief" not in data:
        raise ValueError("Missing 'call_brief' key")
