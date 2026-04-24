"""Normalize raw phone numbers to E.164 format using libphonenumber."""
import re
import phonenumbers


_SEPARATORS_RE = re.compile(r"[;/,]")


def normalize_phone(raw: str | None, country_code: str = "IT") -> str | None:
    """
    Normalize a phone number to E.164 format (+CC...).

    Args:
        raw: Raw phone string from OSM (may contain multiple numbers,
             spaces, dashes, parentheses).
        country_code: ISO-2 country code used as default region when
             the number doesn't have an international prefix.

    Returns:
        E.164 formatted string or None if no valid number could be parsed.
    """
    if not raw or not raw.strip():
        return None

    candidates = _SEPARATORS_RE.split(raw)
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            parsed = phonenumbers.parse(candidate, country_code)
        except phonenumbers.NumberParseException:
            continue
        if not phonenumbers.is_valid_number(parsed):
            continue
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return None
