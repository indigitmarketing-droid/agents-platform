"""Timezone-aware scheduler for triggering scraping at 9am local time."""
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class Target:
    """Subset of scraping_targets row needed for scheduling decisions."""
    id: str
    timezone: str
    enabled: bool
    last_run_at: datetime | None


class TimezoneScheduler:
    """Decides which scraping targets should run NOW based on local time."""

    TRIGGER_HOUR = 9
    WINDOW_MINUTES = 5

    def get_targets_to_run(
        self, targets: list[Target], now_utc: datetime
    ) -> list[Target]:
        result = []
        for target in targets:
            if not target.enabled:
                continue
            tz = ZoneInfo(target.timezone)
            now_local = now_utc.astimezone(tz)
            in_window = (
                now_local.hour == self.TRIGGER_HOUR
                and now_local.minute < self.WINDOW_MINUTES
            )
            if not in_window:
                continue
            if self._already_ran_today(target, now_local, tz):
                continue
            result.append(target)
        return result

    def _already_ran_today(
        self, target: Target, now_local: datetime, tz: ZoneInfo
    ) -> bool:
        if target.last_run_at is None:
            return False
        last_local = target.last_run_at.astimezone(tz)
        return last_local.date() == now_local.date()
