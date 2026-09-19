"""Authentication primitives: password hashing + JWT (spec §36).

Hashing uses PBKDF2-SHA256 from the stdlib (no native deps). Tokens are
JWT HS256 and are delivered via httpOnly cookie.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from apps.api.app.core.config import settings

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, expected = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, AttributeError):
        return False


def create_access_token(subject: str, *, user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "uid": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.auth_access_token_minutes),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.auth_secret_key, algorithms=[settings.auth_algorithm])
