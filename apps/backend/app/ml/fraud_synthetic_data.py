"""Synthetic fraud training data (P2-08) — the SOW explicitly calls for this
("синтетик дайралтын өгөгдөл"), unlike OCR/classifier where a real labeled
dataset is a hard external blocker. Two attack patterns are simulated:

  - "bombing": a burst of many reviews from freshly-created accounts/devices
    in a short window, low PoE, near-identical text.
  - "sleeper": a normal-looking account that waits, then posts one extreme
    review far from the entity's mean rating with no verification evidence.

Normal reviews are generated with the opposite statistical profile. This is
scaffolding to prove the training pipeline works end-to-end, not a substitute
for validating against real attack data before the AUC>=0.93 acceptance is
claimed — see docs/PROGRESS.md.
"""

import random

from app.ml.fraud_features import FraudFeatures

random.seed(42)  # deterministic test data — a fraud-detection test suite that flakes is worse than useless


def _normal_review() -> FraudFeatures:
    return FraudFeatures(
        account_age_hours=random.uniform(24 * 7, 24 * 365 * 2),
        reviews_by_user_last_24h=random.choice([1, 1, 1, 2]),
        reviews_by_device_last_24h=random.choice([1, 1, 2]),
        seconds_since_account_creation_to_review=random.uniform(3600, 3600 * 24 * 30),
        poe_level_numeric=random.choice([2, 3, 3, 4]),
        text_similarity_to_other_reviews_by_user=random.uniform(0.0, 0.3),
        rating_deviation_from_entity_mean=random.uniform(-0.8, 0.8),
        is_first_review_for_entity_from_this_ip_subnet=random.random() < 0.7,
        gps_mock_flag=False,
    )


def _bombing_review() -> FraudFeatures:
    return FraudFeatures(
        account_age_hours=random.uniform(0, 6),
        reviews_by_user_last_24h=random.randint(3, 20),
        reviews_by_device_last_24h=random.randint(5, 50),
        seconds_since_account_creation_to_review=random.uniform(0, 600),
        poe_level_numeric=random.choice([0, 0, 1]),
        text_similarity_to_other_reviews_by_user=random.uniform(0.7, 1.0),
        rating_deviation_from_entity_mean=random.choice([-2.0, -1.8, 2.0]),
        is_first_review_for_entity_from_this_ip_subnet=random.random() < 0.2,
        gps_mock_flag=random.random() < 0.4,
    )


def _sleeper_review() -> FraudFeatures:
    return FraudFeatures(
        account_age_hours=random.uniform(24 * 30, 24 * 200),
        reviews_by_user_last_24h=1,
        reviews_by_device_last_24h=1,
        seconds_since_account_creation_to_review=random.uniform(3600, 3600 * 24 * 60),
        poe_level_numeric=random.choice([0, 1]),
        text_similarity_to_other_reviews_by_user=random.uniform(0.0, 0.2),
        rating_deviation_from_entity_mean=random.choice([-2.2, 2.2]),
        is_first_review_for_entity_from_this_ip_subnet=True,
        gps_mock_flag=random.random() < 0.5,
    )


def generate_synthetic_dataset(*, n_normal: int = 4000, n_bombing: int = 500, n_sleeper: int = 500) -> tuple[list[list[float]], list[int]]:
    rows: list[list[float]] = []
    labels: list[int] = []

    for _ in range(n_normal):
        rows.append(_normal_review().to_vector())
        labels.append(0)
    for _ in range(n_bombing):
        rows.append(_bombing_review().to_vector())
        labels.append(1)
    for _ in range(n_sleeper):
        rows.append(_sleeper_review().to_vector())
        labels.append(1)

    return rows, labels
