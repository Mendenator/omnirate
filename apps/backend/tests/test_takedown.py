from datetime import datetime, timedelta

from app.domain.takedown import RequesterType, TakedownStatus, check_sla, compute_sla_deadline

NOW = datetime(2026, 9, 22, 12, 0, 0)


def test_user_request_gets_72h_sla():
    deadline = compute_sla_deadline(requester_type=RequesterType.USER, created_at=NOW)
    assert deadline == NOW + timedelta(hours=72)


def test_law_enforcement_request_gets_4h_sla():
    deadline = compute_sla_deadline(requester_type=RequesterType.LAW_ENFORCEMENT, created_at=NOW)
    assert deadline == NOW + timedelta(hours=4)


def test_sla_not_breached_when_time_remains():
    deadline = NOW + timedelta(hours=2)
    result = check_sla(deadline=deadline, now=NOW, status=TakedownStatus.OPEN)
    assert result.is_breached is False
    assert result.hours_remaining == 2.0


def test_sla_breached_when_deadline_passed():
    deadline = NOW - timedelta(hours=1)
    result = check_sla(deadline=deadline, now=NOW, status=TakedownStatus.OPEN)
    assert result.is_breached is True


def test_resolved_request_is_never_breached_even_past_deadline():
    deadline = NOW - timedelta(hours=100)
    result = check_sla(deadline=deadline, now=NOW, status=TakedownStatus.RESOLVED)
    assert result.is_breached is False
