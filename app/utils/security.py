import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from jose import jwt, JWTError, ExpiredSignatureError

from app.exceptions import UnauthorizedError


PBKDF2_ROUNDS = 120_000
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, stored_hash = password_hash.split("$", 1)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return hmac.compare_digest(digest.hex(), stored_hash)


def create_access_token(subject: str, secret_key: str, expires_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }

    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict[str, int | str]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload

    except ExpiredSignatureError:
        raise UnauthorizedError("Token expired")

    except JWTError:
        raise UnauthorizedError("Invalid token")