import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY was not found. Add it to Backend/.env."
    )


ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Converts a plain password into a secure Argon2 hash.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Checks whether the entered password matches the stored hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(subject: str) -> str:
    """
    Creates a signed JWT token for an authenticated user.
    """

    current_time = datetime.now(timezone.utc)

    expiration_time = current_time + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    token_payload = {
        "sub": subject,
        "iat": current_time,
        "exp": expiration_time,
    }

    return jwt.encode(
        token_payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Verifies a JWT token and returns its payload.
    """

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )