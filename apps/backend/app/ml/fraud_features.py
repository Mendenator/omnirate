"""Fraud feature schema (P2-08), shared by the synthetic data generator and
the real feature-extraction path (not yet wired to live data — see
docs/PROGRESS.md; this module defines *what* a feature vector looks like so
training and inference can't drift apart).
"""

from dataclasses import dataclass, fields

FEATURE_NAMES = (
    "account_age_hours",
    "reviews_by_user_last_24h",
    "reviews_by_device_last_24h",
    "seconds_since_account_creation_to_review",
    "poe_level_numeric",  # 0-4, from app.domain.poe.PoeLevel
    "text_similarity_to_other_reviews_by_user",  # 0-1, max cosine sim vs their own review history
    "rating_deviation_from_entity_mean",
    "is_first_review_for_entity_from_this_ip_subnet",
    "gps_mock_flag",
)


@dataclass(frozen=True)
class FraudFeatures:
    account_age_hours: float
    reviews_by_user_last_24h: int
    reviews_by_device_last_24h: int
    seconds_since_account_creation_to_review: float
    poe_level_numeric: int
    text_similarity_to_other_reviews_by_user: float
    rating_deviation_from_entity_mean: float
    is_first_review_for_entity_from_this_ip_subnet: bool
    gps_mock_flag: bool

    def to_vector(self) -> list[float]:
        return [float(getattr(self, f.name)) for f in fields(self)]


assert FEATURE_NAMES == tuple(f.name for f in fields(FraudFeatures))
