"""US business hours + Do Not Call check for Setting Agent."""
from datetime import datetime
from zoneinfo import ZoneInfo


US_TIMEZONE = "America/New_York"
US_BUSINESS_HOURS_START = 8
US_BUSINESS_HOURS_END = 21


def is_within_business_hours(now_utc: datetime, tz: str = US_TIMEZONE) -> bool:
    """Check if it's currently within legal calling hours.
    US rules: 8am-9pm local time, Monday-Saturday (no Sunday).
    """
    local = now_utc.astimezone(ZoneInfo(tz))
    if local.weekday() == 6:  # Sunday
        return False
    return US_BUSINESS_HOURS_START <= local.hour < US_BUSINESS_HOURS_END


def is_phone_in_dnc(phone: str, supabase_client) -> bool:
    """Check if phone is in our internal do_not_call table."""
    result = (
        supabase_client.table("do_not_call")
        .select("phone")
        .eq("phone", phone)
        .limit(1)
        .execute()
    )
    rows = result.data if result is not None else None
    return bool(rows)
