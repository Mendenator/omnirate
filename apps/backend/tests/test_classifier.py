from app.ml.classifier import classify_toxicity


def test_clean_text_is_not_toxic():
    result = classify_toxicity("Энэ ресторан их сайхан байсан")
    assert result.is_toxic is False
    assert result.toxicity_score == 0.0


def test_flagged_keyword_raises_score():
    result = classify_toxicity("чи новш хүн байна")
    assert result.toxicity_score > 0


def test_result_reports_model_name_for_auditability():
    result = classify_toxicity("сайн байна")
    assert result.model == "heuristic-v0"
