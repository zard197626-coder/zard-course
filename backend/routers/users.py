"""用户中心：商品、收藏、留言、资料与密码。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..auth import CurrentUser, hash_password, verify_password
from ..database import Database, iso_now
from ..deps import get_db
from ..responses import ApiError, ok
from ..schemas import PasswordChangeRequest, ProfileUpdateRequest
from ..serializers import message_data, pagination, product_data, public_user
from .products import PRODUCT_SELECT

router = APIRouter(prefix="/api/users", tags=["用户中心"])


@router.get("/me")
def my_profile(user: CurrentUser):
    return ok(public_user(user))


@router.put("/me")
def update_profile(
    payload: ProfileUpdateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    changes = {key: value for key, value in payload.model_dump(exclude_unset=True).items() if value is not None}
    if not changes:
        raise ApiError(422, "没有可更新的字段", "NO_CHANGES")
    assignments = ", ".join(f"{field} = ?" for field in changes)
    db.execute(
        f"UPDATE users SET {assignments} WHERE id = ?",
        tuple(changes.values()) + (user["id"],),
    )
    row = db.fetch_one("SELECT * FROM users WHERE id = ?", (user["id"],))
    return ok(public_user(row), "个人资料已更新")


@router.put("/me/password")
def change_password(
    payload: PasswordChangeRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    if not verify_password(payload.current_password, user["password_hash"]):
        raise ApiError(400, "当前密码不正确", "WRONG_PASSWORD")
    if payload.current_password == payload.new_password:
        raise ApiError(400, "新密码不能与当前密码相同", "SAME_PASSWORD")
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(payload.new_password), user["id"]),
    )
    # 保留当前会话，注销该账号的其他会话。
    current_hash = user.get("current_token_hash")
    if current_hash:
        db.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
            (user["id"], current_hash),
        )
    return ok(None, "密码已修改，其他设备上的登录已失效")


@router.get("/me/products")
def my_products(
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
    status: str | None = Query(default=None),
):
    conditions = ["p.seller_id = ?", "p.is_deleted = 0"]
    params: list[object] = [user["id"]]
    if status:
        if status not in ("在售", "已预订", "已售出", "已下架"):
            raise ApiError(422, "商品状态筛选不合法", "INVALID_STATUS")
        conditions.append("p.status = ?")
        params.append(status)
    rows = db.fetch_all(
        PRODUCT_SELECT
        + " WHERE "
        + " AND ".join(conditions)
        + " ORDER BY p.created_at DESC, p.id DESC",
        tuple(params),
    )
    return ok({"items": [product_data(dict(row)) for row in rows], "total": len(rows)})


@router.get("/me/favorites")
def my_favorites(
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
):
    total_row = db.fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM favorites f JOIN products p ON p.id = f.product_id
        WHERE f.user_id = ? AND p.is_deleted = 0 AND p.status != '已下架'
        """,
        (user["id"],),
    )
    total = int(total_row["total"]) if total_row else 0
    rows = db.fetch_all(
        PRODUCT_SELECT
        + """
        JOIN favorites fav ON fav.product_id = p.id
        WHERE fav.user_id = ? AND p.is_deleted = 0 AND p.status != '已下架'
        ORDER BY fav.created_at DESC, fav.id DESC
        LIMIT ? OFFSET ?
        """,
        (user["id"], page_size, (page - 1) * page_size),
    )
    items = []
    for row in rows:
        data = product_data(dict(row))
        data["is_favorited"] = True
        items.append(data)
    return ok({"items": items, "pagination": pagination(page, page_size, total)})


@router.get("/me/messages")
def my_messages(
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
    scope: str = Query(default="authored", pattern="^(authored|received)$"),
):
    if scope == "authored":
        condition = "m.user_id = ?"
        params: tuple[object, ...] = (user["id"],)
    else:
        condition = "p.seller_id = ?"
        params = (user["id"],)
    rows = db.fetch_all(
        f"""
        SELECT m.*, p.name AS product_name, p.status AS product_status,
               u.username AS author_username,
               u.display_name AS author_display_name,
               u.avatar_url AS author_avatar_url
        FROM messages m
        JOIN products p ON p.id = m.product_id
        JOIN users u ON u.id = m.user_id
        WHERE {condition} AND p.is_deleted = 0
        ORDER BY m.created_at DESC, m.id DESC
        """,
        params,
    )
    items = []
    for row in rows:
        data = dict(row)
        data["can_delete"] = bool(user["role"] == "admin" or int(data["user_id"]) == int(user["id"]))
        message = message_data(data)
        message["product"] = {
            "id": data["product_id"],
            "name": data["product_name"],
            "status": data["product_status"],
        }
        items.append(message)
    return ok({"items": items, "total": len(items), "scope": scope})
