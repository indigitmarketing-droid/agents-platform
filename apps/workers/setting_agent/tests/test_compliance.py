from datetime import datetime, timezone
from unittest.mock import MagicMock
from apps.workers.setting_agent.compliance import (
    is_within_business_hours,
    is_phone_in_dnc,
    US_TIMEZONE,
)


def test_business_hours_monday_10am_et_is_valid():
    # 10am ET on a Monday (2026-04-27 is Monday) = 14:00 UTC (EDT is UTC-4)
    now_utc = datetime(2026, 4, 27, 14, 0, 0, tzinfo=timezone.utc)
    assert is_within_business_hours(now_utc) is True


def test_business_hours_sunday_blocked():
    # Sunday 2026-04-26 at 14:00 UTC = 10am ET
    now_utc = datetime(2026, 4, 26, 14, 0, 0, tzinfo=timezone.utc)
    assert is_within_business_hours(now_utc) is False


def test_business_hours_too_early():
    # 7am ET on Monday = 11:00 UTC
    now_utc = datetime(2026, 4, 27, 11, 0, 0, tzinfo=timezone.utc)
    assert is_within_business_hours(now_utc) is False


def test_business_hours_too_late():
    # 9:30pm ET on Monday = 01:30 UTC next day
    now_utc = datetime(2026, 4, 28, 1, 30, 0, tzinfo=timezone.utc)
    assert is_within_business_hours(now_utc) is False


def test_business_hours_8pm_et_still_valid():
    # 8pm ET = 00:00 UTC next day
    now_utc = datetime(2026, 4, 28, 0, 0, 0, tzinfo=timezone.utc)
    assert is_within_business_hours(now_utc) is True


def test_dnc_check_phone_in_table():
    client = MagicMock()
    table = MagicMock()
    select = MagicMock()
    eq = MagicMock()
    eq.limit = MagicMock(return_value=eq)
    eq.execute = MagicMock(return_value=MagicMock(data=[{"phone": "+15551234567"}]))
    select.eq.return_value = eq
    table.select.return_value = select
    client.table.return_value = table

    assert is_phone_in_dnc("+15551234567", client) is True


def test_dnc_check_phone_not_in_table():
    client = MagicMock()
    table = MagicMock()
    select = MagicMock()
    eq = MagicMock()
    eq.limit = MagicMock(return_value=eq)
    eq.execute = MagicMock(return_value=MagicMock(data=[]))
    select.eq.return_value = eq
    table.select.return_value = select
    client.table.return_value = table

    assert is_phone_in_dnc("+15551234567", client) is False
