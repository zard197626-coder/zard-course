"""注册、登录、退出和当前用户接口。"""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from ..auth import (
    CurrentUser,
    authenticate,
    create_session,
    hash_password,
    prune_expired_sessions,
)
from ..database import Database, iso_now
from ..deps import get_db
from ..responses import ApiError, ok
from ..schemas import LoginRequest, RegisterRequest
from ..serializers import public_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", status_code=201)
def register(
    payload: RegisterRequest,
    db: Annotated[Database, Depends(get_db)],
):
    duplicate = db.fetch_one(
        "SELECT username, email FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
        (payload.username, payload.email),
    )
    if duplicate is not None:
        if str(duplicate["username"]).lower() == payload.username.lower():
            raise ApiError(409, "用户名已被使用", "USERNAME_TAKEN")
        raise ApiError(409, "邮箱已被注册", "EMAIL_TAKEN")

    now = iso_now()
    try:
        with db.transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users
                    (username, email, password_hash, display_name, is_student,
                     role, campus, bio, avatar_url, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 'user', ?, '', '', 1, ?)
                """,
                (
                    payload.username,
                    payload.email,
                    hash_password(payload.password),
                    payload.display_name or payload.username,
                    int(payload.is_student),
                    payload.campus,
                    now,
                ),
            )
            user_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "用户名或邮箱已被使用", "USER_EXISTS") from exc

    user = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    token = create_session(db, user_id)
    return ok(
        {"token": token, "token_type": "Bearer", "user": public_user(user)},
        "注册成功",
        201,
    )


@router.post("/login")
def login(
    payload: LoginRequest,
    db: Annotated[Database, Depends(get_db)],
):
    prune_expired_sessions(db)
    user = authenticate(db, payload.username, payload.password)
    token = create_session(db, int(user["id"]))
    return ok(
        {"token": token, "token_type": "Bearer", "user": public_user(user)},
        "登录成功",
    )


@router.post("/logout")
def logout(
    request: Request,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    token_hash = getattr(request.state, "token_hash", None)
    if token_hash:
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    return ok(None, "已退出登录")


@router.get("/me")
def me(user: CurrentUser):
    return ok(public_user(user))
