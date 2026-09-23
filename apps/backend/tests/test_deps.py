import uuid

import pytest
from fastapi import HTTPException

from app.core.deps import get_current_user
from app.core.security import issue_access_token


async def test_missing_bearer_prefix_rejected():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="not-a-bearer-token")
    assert exc_info.value.status_code == 401


async def test_malformed_token_rejected():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer not-a-real-jwt")
    assert exc_info.value.status_code == 401


async def test_valid_token_returns_current_user():
    user_id = uuid.uuid4()
    token = issue_access_token(subject_id=str(user_id), rd_hash="rd-hash-abc", poe_level="L2")

    current = await get_current_user(authorization=f"Bearer {token}")

    assert current.user_id == user_id
    assert current.rd_hash == "rd-hash-abc"
    assert current.poe_level == "L2"


async def test_missing_poe_level_claim_defaults_to_l0():
    # issue_access_token always sets poe_level, so hit the .get() default
    # directly rather than depending on that invariant holding forever.
    import jwt

    from app.core.config import get_settings

    settings = get_settings()
    claims = {"sub": str(uuid.uuid4()), "rd_hash": "abc"}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    current = await get_current_user(authorization=f"Bearer {token}")

    assert current.poe_level == "L0"
