from sklearn.metrics import roc_auc_score

from app.ml.fraud_features import FraudFeatures
from app.ml.fraud_model import predict_fraud_score, train_fraud_model
from app.ml.fraud_synthetic_data import generate_synthetic_dataset


def test_trained_model_separates_synthetic_fraud_from_normal():
    rows, labels = generate_synthetic_dataset(n_normal=1000, n_bombing=150, n_sleeper=150)

    split = int(len(rows) * 0.8)
    train_rows, test_rows = rows[:split], rows[split:]
    train_labels, test_labels = labels[:split], labels[split:]

    model = train_fraud_model(train_rows, train_labels, num_boost_round=100)
    predictions = model.predict(test_rows)

    auc = roc_auc_score(test_labels, predictions)
    # Synthetic patterns are deliberately well-separated (see
    # fraud_synthetic_data.py's docstring) — a real-data retrain will land
    # lower than this; the SOW's 0.93 target is validated there, not here.
    assert auc > 0.9


def test_predict_fraud_score_returns_probability_in_range():
    rows, labels = generate_synthetic_dataset(n_normal=200, n_bombing=50, n_sleeper=50)
    model = train_fraud_model(rows, labels, num_boost_round=50)

    bombing_like = FraudFeatures(
        account_age_hours=1,
        reviews_by_user_last_24h=15,
        reviews_by_device_last_24h=30,
        seconds_since_account_creation_to_review=60,
        poe_level_numeric=0,
        text_similarity_to_other_reviews_by_user=0.95,
        rating_deviation_from_entity_mean=2.0,
        is_first_review_for_entity_from_this_ip_subnet=False,
        gps_mock_flag=True,
    )
    score = predict_fraud_score(model, bombing_like)
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # should lean toward "fraud" given an obviously bombing-shaped input
