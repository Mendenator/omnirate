from datetime import datetime, timedelta

from app.domain.geofence import (
    GpsPing,
    compute_dwell_seconds,
    detect_mock_location,
    detect_speed_jump,
    haversine_distance_km,
    is_within_geofence,
)

UB_CENTER = (47.9184, 106.9177)  # Ulaanbaatar city center, used as a stable reference point


def _ping(lat, lon, minutes_offset, accuracy=8.0, is_mock=False, base=None):
    base = base or datetime(2026, 9, 22, 12, 0, 0)
    return GpsPing(lat=lat, lon=lon, accuracy_m=accuracy, is_mock_provider_flag=is_mock, recorded_at=base + timedelta(minutes=minutes_offset))


def test_haversine_zero_distance_for_identical_points():
    assert haversine_distance_km(47.9, 106.9, 47.9, 106.9) == 0.0


def test_haversine_known_distance_ub_to_darkhan_roughly_correct():
    # Ulaanbaatar to Darkhan is ~215km by straight-line distance.
    darkhan = (49.4867, 105.9228)
    distance = haversine_distance_km(*UB_CENTER, *darkhan)
    assert 190 < distance < 230


def test_is_within_geofence_true_for_center_point():
    assert is_within_geofence(_ping(*UB_CENTER, 0), center_lat=UB_CENTER[0], center_lon=UB_CENTER[1], radius_m=50) is True


def test_is_within_geofence_false_for_far_point():
    far = _ping(49.4867, 105.9228, 0)
    assert is_within_geofence(far, center_lat=UB_CENTER[0], center_lon=UB_CENTER[1], radius_m=50) is False


def test_dwell_seconds_sums_consecutive_inside_pings():
    pings = [_ping(*UB_CENTER, 0), _ping(*UB_CENTER, 5), _ping(*UB_CENTER, 10)]
    dwell = compute_dwell_seconds(pings, center_lat=UB_CENTER[0], center_lon=UB_CENTER[1], radius_m=50)
    assert dwell == 600.0  # 10 minutes = 600s


def test_dwell_seconds_excludes_time_outside_geofence():
    far = (49.4867, 105.9228)
    pings = [_ping(*UB_CENTER, 0), _ping(*far, 5), _ping(*UB_CENTER, 10)]
    dwell = compute_dwell_seconds(pings, center_lat=UB_CENTER[0], center_lon=UB_CENTER[1], radius_m=50)
    assert dwell == 0.0  # never two consecutive inside pings


def test_detect_speed_jump_flags_impossible_travel():
    darkhan = (49.4867, 105.9228)
    pings = [_ping(*UB_CENTER, 0), _ping(*darkhan, 1)]  # 215km in 1 minute
    anomalies = detect_speed_jump(pings)
    assert len(anomalies) == 1
    assert anomalies[0][2] > 150


def test_detect_speed_jump_ignores_plausible_walking_speed():
    pings = [_ping(47.9184, 106.9177, 0), _ping(47.9185, 106.9178, 5)]
    assert detect_speed_jump(pings) == []


def test_detect_mock_location_via_os_flag():
    pings = [_ping(*UB_CENTER, 0, is_mock=True)]
    assert detect_mock_location(pings) is True


def test_detect_mock_location_via_speed_jump():
    darkhan = (49.4867, 105.9228)
    pings = [_ping(*UB_CENTER, 0), _ping(*darkhan, 1)]
    assert detect_mock_location(pings) is True


def test_detect_mock_location_via_suspiciously_uniform_accuracy():
    pings = [_ping(*UB_CENTER, i, accuracy=1.0) for i in range(3)]
    assert detect_mock_location(pings) is True


def test_detect_mock_location_false_for_normal_pings():
    pings = [_ping(47.9184, 106.9177, 0, accuracy=8.0), _ping(47.9185, 106.9178, 5, accuracy=12.0)]
    assert detect_mock_location(pings) is False
