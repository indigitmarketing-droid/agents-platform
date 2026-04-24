from datetime import datetime, timezone

from apps.workers.scraping_worker.scheduler import TimezoneScheduler, Target


def make_target(tz="Europe/Rome", last_run_at=None, enabled=True, target_id="t1"):
    return Target(
        id=target_id,
        timezone=tz,
        enabled=enabled,
        last_run_at=last_run_at,
    )


def test_returns_target_at_9am_local():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    result = sched.get_targets_to_run(targets, now_utc)
    assert len(result) == 1


def test_skip_if_not_9am():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 8, 30, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    result = sched.get_targets_to_run(targets, now_utc)
    assert len(result) == 0


def test_window_includes_minutes_0_to_4():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 4, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 1


def test_window_excludes_minute_5():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 5, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_skip_disabled_target():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", enabled=False)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_skip_if_already_ran_today_local():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    last = datetime(2026, 4, 9, 6, 50, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", last_run_at=last)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_run_if_last_run_was_yesterday_local():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    last = datetime(2026, 4, 8, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", last_run_at=last)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 1


def test_multiple_timezones_only_one_matches():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [
        make_target("Europe/Rome", target_id="rome"),
        make_target("America/New_York", target_id="ny"),
    ]
    result = sched.get_targets_to_run(targets, now_utc)
    ids = [t.id for t in result]
    assert "rome" in ids
    assert "ny" not in ids


def test_dataclass_target_round_trip():
    t = Target(
        id="abc",
        timezone="Europe/Rome",
        enabled=True,
        last_run_at=None,
    )
    assert t.id == "abc"
    assert t.enabled is True
