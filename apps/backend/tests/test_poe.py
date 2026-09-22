from app.domain.poe import PoeLevel, counts_as_verified, evidence_kinds_to_level, poe_weight


def test_e_barimt_evidence_yields_l4():
    assert evidence_kinds_to_level({"e_barimt"}) == PoeLevel.L4


def test_e_barimt_outranks_other_evidence_present():
    assert evidence_kinds_to_level({"gps", "ocr_receipt", "e_barimt"}) == PoeLevel.L4


def test_ocr_receipt_without_e_barimt_yields_l3():
    assert evidence_kinds_to_level({"ocr_receipt", "gps"}) == PoeLevel.L3


def test_gps_only_yields_l2():
    assert evidence_kinds_to_level({"gps"}) == PoeLevel.L2


def test_no_evidence_yields_l1():
    assert evidence_kinds_to_level(set()) == PoeLevel.L1


def test_l2_and_above_count_as_verified_for_k3():
    assert counts_as_verified("L2") is True
    assert counts_as_verified("L3") is True
    assert counts_as_verified("L4") is True
    assert counts_as_verified("L1") is False
    assert counts_as_verified("L0") is False


def test_weights_are_monotonic_increasing():
    levels = [PoeLevel.L0, PoeLevel.L1, PoeLevel.L2, PoeLevel.L3, PoeLevel.L4]
    weights = [poe_weight(level) for level in levels]
    assert weights == sorted(weights)
    assert weights[0] == 0.0
    assert weights[-1] == 1.0
