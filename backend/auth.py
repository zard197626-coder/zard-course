"""密码哈希、会话 Token 与登录依赖。"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Annotated

from fastapi import Depends, Header, Request

from .database import Database, iso_now, utc_now
from .responses import ApiError

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 310_000
SESSION_TTL_HOURS = max(1, int(os.getenv("SESSION_TTL_HOURS", "72")))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"), PBKDF2_ITERATIONS
    )
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected = encoded.split("$", 3)
        if algorithm != PBKDF2_ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            int(iterations_text),
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Database, user_id: int, ttl_hours: int | None = None) -> str:
    token = secrets.token_urlsafe(32)
    now = utc_now()
    expires = now + timedelta(hours=ttl_hours or SESSION_TTL_HOURS)
    db.execute(
        "INSERT INTO sessions (user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, hash_token(token), now.isoformat(timespec="seconds"), expires.isoformat(timespec="seconds")),
    )
    return token


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _lookup_user(request: Request, token: str) -> dict[str, Any] | None:
    db: Database = request.app.state.db
    token_hash = hash_token(token)
    row = db.fetch_one(
        """
        SELECT u.*, s.expires_at, s.token_hash
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        """,
        (token_hash,),
    )
    if row is None:
        return None
    try:
        expires = datetime.fromisoformat(str(row["expires_at"]))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
    except ValueError:
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        return None
    if expires <= utc_now():
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        return None
    if not row["is_active"]:
        return None
    user = dict(row)
    user.pop("token_hash", None)
    user.pop("expires_at", None)
    user["current_token_hash"] = token_hash
    request.state.token_hash = token_hash
    return user


def get_optional_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any] | None:
    token = _bearer_token(authorization)
    if not token:
        return None
    return _lookup_user(request, token)


def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    token = _bearer_token(authorization)
    if not token:
        raise ApiError(401, "请先登录", "UNAUTHORIZED")
    user = _lookup_user(request, token)
    if user is None:
        raise ApiError(401, "登录已失效，请重新登录", "INVALID_TOKEN")
    return user


def require_admin(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    if user["role"] != "admin":
        raise ApiError(403, "需要管理员权限", "FORBIDDEN")
    return user


def authenticate(db: Database, account: str, password: str) -> dict[str, Any]:
    row = db.fetch_one(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
        (account.strip(), account.strip()),
    )
    if row is None or not verify_password(password, row["password_hash"]):
        raise ApiError(401, "账号或密码错误", "INVALID_CREDENTIALS")
    if not row["is_active"]:
        raise ApiError(403, "账号已被停用，请联系管理员", "ACCOUNT_DISABLED")
    return dict(row)


def prune_expired_sessions(db: Database) -> None:
    db.execute("DELETE FROM sessions WHERE expires_at <= ?", (iso_now(),))


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
OptionalUser = Annotated[dict[str, Any] | None, Depends(get_optional_user)]
AdminUser = Annotated[dict[str, Any], Depends(require_admin)]
