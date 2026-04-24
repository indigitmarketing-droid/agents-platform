import pytest
from apps.workers.scraping_worker.phone_normalizer import normalize_phone


def test_normalize_italian_with_prefix():
    result = normalize_phone("+39 02 12345678", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_italian_without_prefix():
    result = normalize_phone("02 12345678", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_strips_spaces_and_dashes():
    result = normalize_phone("+39-02-1234-5678", "IT")
    assert result is not None
    assert " " not in result
    assert "-" not in result


def test_normalize_returns_first_when_multiple():
    result = normalize_phone("+39 02 12345678; +39 339 9999999", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_returns_first_with_slash():
    result = normalize_phone("02 12345678 / 339 9999999", "IT")
    assert result is not None


def test_normalize_invalid_returns_none():
    assert normalize_phone("not a phone", "IT") is None
    assert normalize_phone("123", "IT") is None
    assert normalize_phone("", "IT") is None


def test_normalize_french_number():
    result = normalize_phone("+33 1 23 45 67 89", "FR")
    assert result is not None
    assert result.startswith("+33")


def test_normalize_us_number():
    result = normalize_phone("+1 415 555 1234", "US")
    assert result is not None
    assert result.startswith("+1")
