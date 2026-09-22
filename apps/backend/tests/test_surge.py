from app.domain.surge import check_surge, compute_z_score


def test_z_score_zero_for_average_count():
    history = [10, 12, 9, 11, 10, 10]
    assert compute_z_score(10, history) == 0.0 or abs(compute_z_score(10, history)) < 0.5


def test_z_score_high_for_spike():
    history = [10, 11, 9, 10, 12, 10]
    z = compute_z_score(50, history)
    assert z > 4


def test_check_surge_requires_minimum_history():
    result = check_surge(100, [10, 12])  # too little history
    assert result.is_surge is False


def test_check_surge_flags_spike_with_enough_history():
    history = [10, 11, 9, 10, 12, 10]
    result = check_surge(60, history)
    assert result.is_surge is True
    assert result.z_score > 4


def test_check_surge_does_not_flag_normal_variation():
    history = [10, 11, 9, 10, 12, 10]
    result = check_surge(11, history)
    assert result.is_surge is False


def test_zero_stdev_no_change_yields_zero_z_score():
    history = [10, 10, 10, 10, 10, 10]
    assert compute_z_score(10, history) == 0.0
