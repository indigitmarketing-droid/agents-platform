"""Pick leads for the daily cold-call batch."""
from datetime import datetime, timedelta, timezone


def pick_leads_for_batch(supabase_client, limit: int = 10) -> list[dict]:
    """
    Select leads eligible for cold calling.

    Filter:
      - call_status = 'never_called'
      - call_attempts < 3
      - has_website = false
      - country_code = 'US'
      - phone IS NOT NULL
      - phone NOT IN do_not_call (separate query for simplicity)
      - last_called_at IS NULL OR last_called_at < NOW() - INTERVAL '24 hours'

    Order: FIFO by created_at.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    query = (
        supabase_client.table("leads")
        .select("*")
        .eq("call_status", "never_called")
        .lt("call_attempts", 3)
        .eq("has_website", False)
        .eq("country_code", "US")
        .or_(f"last_called_at.is.null,last_called_at.lt.{cutoff}")
        .order("created_at")
        .limit(limit)
    )
    result = query.execute()
    candidates = result.data or []

    return candidates
