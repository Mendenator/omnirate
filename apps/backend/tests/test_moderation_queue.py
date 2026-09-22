import pytest

from app.domain.moderation_queue import CaseState, Decision, Verdict, resolve_case


def test_no_decisions_awaits_first():
    outcome = resolve_case([])
    assert outcome.state == CaseState.AWAITING_FIRST_DECISION
    assert outcome.final_verdict is None


def test_one_decision_awaits_second():
    outcome = resolve_case([Decision("mod-1", Verdict.APPROVE)])
    assert outcome.state == CaseState.AWAITING_SECOND_DECISION


def test_two_agreeing_decisions_resolve():
    outcome = resolve_case([Decision("mod-1", Verdict.REJECT), Decision("mod-2", Verdict.REJECT)])
    assert outcome.state == CaseState.RESOLVED
    assert outcome.final_verdict == Verdict.REJECT


def test_two_disagreeing_decisions_escalate():
    outcome = resolve_case([Decision("mod-1", Verdict.APPROVE), Decision("mod-2", Verdict.REJECT)])
    assert outcome.state == CaseState.ESCALATED
    assert outcome.final_verdict is None


def test_same_moderator_twice_is_rejected():
    with pytest.raises(ValueError):
        resolve_case([Decision("mod-1", Verdict.APPROVE), Decision("mod-1", Verdict.REJECT)])
