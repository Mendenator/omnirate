"""Jurisdiction-separated scoring for political entities (P3-02).

Acceptance: "2 төрлийн дундаж тусдаа харагдах" — in-jurisdiction (people who
can actually vote for this politician) and out-of-jurisdiction averages are
computed and shown separately, never blended into one number. Blending them
would let a politician's national visibility drown out what their own
constituents think, or vice versa — the whole point of the split.
"""

from dataclasses import dataclass

from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score

DEFAULT_PRIOR_CONFIDENCE = 10.0


@dataclass(frozen=True)
class ReviewWithJurisdiction:
    review: ScoredReview
    is_in_jurisdiction: bool


@dataclass(frozen=True)
class JurisdictionScores:
    in_jurisdiction_score: float | None
    in_jurisdiction_count: int
    out_of_jurisdiction_score: float | None
    out_of_jurisdiction_count: int


def compute_jurisdiction_separated_scores(
    reviews: list[ReviewWithJurisdiction], *, prior_mean: float, prior_confidence: float = DEFAULT_PRIOR_CONFIDENCE
) -> JurisdictionScores:
    in_juris = [r.review for r in reviews if r.is_in_jurisdiction]
    out_juris = [r.review for r in reviews if not r.is_in_jurisdiction]

    return JurisdictionScores(
        in_jurisdiction_score=compute_bayesian_trimmed_score(in_juris, prior_mean=prior_mean, prior_confidence=prior_confidence)
        if in_juris
        else None,
        in_jurisdiction_count=len(in_juris),
        out_of_jurisdiction_score=compute_bayesian_trimmed_score(out_juris, prior_mean=prior_mean, prior_confidence=prior_confidence)
        if out_juris
        else None,
        out_of_jurisdiction_count=len(out_juris),
    )
