import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional


def generate_magic_token() -> str:
    """32-char hex random token (raw — prefixed sb_ in URLs)."""
    return secrets.token_hex(16)


def hash_token(raw_token: str) -> str:
    """SHA-256 hash for DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def make_magic_link(base_url: str, raw_token: str) -> str:
    return f"{base_url}/?token=sb_{raw_token}"


def token_is_valid(token_doc: dict) -> tuple[bool, Optional[str]]:
    if not token_doc:
        return False, "Token not found"
    if token_doc.get("token_used"):
        return False, "Token already used"
    expires_at = token_doc.get("token_expires_at")
    if expires_at:
        exp = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return False, "Token expired"
    return True, None
