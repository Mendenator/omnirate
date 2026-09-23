import pytest

from app.core.config import Settings


def test_dev_env_allows_placeholder_secrets():
    settings = Settings(env="dev")
    assert settings.jwt_secret  # doesn't raise


def test_non_dev_env_rejects_placeholder_secret():
    with pytest.raises(ValueError, match="jwt_secret"):
        Settings(env="prod", jwt_secret="dev-only-change-me-0123456789ab", rd_hmac_secret="x" * 32)


def test_non_dev_env_rejects_short_secret():
    with pytest.raises(ValueError, match="rd_hmac_secret"):
        Settings(env="stage", jwt_secret="x" * 32, rd_hmac_secret="too-short")


def test_non_dev_env_accepts_real_secrets():
    settings = Settings(env="prod", jwt_secret="a" * 32, rd_hmac_secret="b" * 32)
    assert settings.env == "prod"
