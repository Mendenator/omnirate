from datetime import datetime, timedelta

from app.domain.device_binding import KnownLocation, detect_impossible_travel, is_device_in_cooldown

NOW = datetime(2026, 9, 22, 12, 0, 0)


def test_brand_new_device_is_in_cooldown():
    assert is_device_in_cooldown(first_seen_at=NOW, now=NOW + timedelta(days=1)) is True


def test_device_seen_over_7_days_ago_is_not_in_cooldown():
    assert is_device_in_cooldown(first_seen_at=NOW - timedelta(days=8), now=NOW) is False


def test_device_exactly_at_boundary_is_not_in_cooldown():
    assert is_device_in_cooldown(first_seen_at=NOW - timedelta(days=7), now=NOW) is False


def test_impossible_travel_detected_for_ub_to_darkhan_in_minutes():
    ub = KnownLocation(lat=47.9184, lon=106.9177, seen_at=NOW)
    darkhan = KnownLocation(lat=49.4867, lon=105.9228, seen_at=NOW + timedelta(minutes=10))
    assert detect_impossible_travel(ub, darkhan) is True


def test_plausible_travel_not_flagged():
    a = KnownLocation(lat=47.9184, lon=106.9177, seen_at=NOW)
    b = KnownLocation(lat=47.9195, lon=106.9188, seen_at=NOW + timedelta(minutes=10))
    assert detect_impossible_travel(a, b) is False


def test_non_positive_time_delta_is_flagged_as_impossible():
    a = KnownLocation(lat=47.9184, lon=106.9177, seen_at=NOW)
    b = KnownLocation(lat=48.0, lon=107.0, seen_at=NOW)  # same/earlier timestamp, different place
    assert detect_impossible_travel(a, b) is True
