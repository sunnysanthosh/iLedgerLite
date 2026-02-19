"""
Shared JWT token verification for non-auth services.

Each service copies this pattern and adjusts the user lookup
to match its own database models and session setup.
"""

from jose import JWTError, jwt


def decode_access_token(token: str, secret: str, algorithm: str = "HS256") -> dict | None:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
