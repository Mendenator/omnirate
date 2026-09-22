import uuid

from fastapi import Header, HTTPException

from app.core.security import decode_access_token


class CurrentUser:
    def __init__(self, user_id: uuid.UUID, rd_hash: str, poe_level: str):
        self.user_id = user_id
        self.rd_hash = rd_hash
        self.poe_level = poe_level


async def get_current_user(authorization: str = Header(...)) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        claims = decode_access_token(token)
    except Exception as exc:  # jose raises various JWTError subclasses
        raise HTTPException(status_code=401, detail="invalid token") from exc
    return CurrentUser(
        user_id=uuid.UUID(claims["sub"]),
        rd_hash=claims["rd_hash"],
        poe_level=claims.get("poe_level", "L0"),
    )
