"""商品、收藏与留言接口。"""

from __future__ import annotations

import math
import sqlite3
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from ..auth import CurrentUser, OptionalUser
from ..database import Database, iso_now
from ..deps import get_db
from ..models import PRODUCT_CATEGORIES, PRODUCT_STATUSES
from ..money import money_text
from ..responses import ApiError, ok
from ..schemas import MessageCreateRequest, ProductCreateRequest, ProductUpdateRequest
from ..serializers import message_data, pagination, product_data

router = APIRouter(prefix="/api", tags=["商品"])

PRODUCT_SELECT = """
SELECT p.*,
       u.username AS seller_username,
       u.display_name AS seller_display_name,
       u.avatar_url AS seller_avatar_url,
       u.campus AS seller_campus,
       u.is_student AS seller_is_student,
       (SELECT COUNT(*) FROM favorites f WHERE f.product_id = p.id) AS favorite_count,
       (SELECT COUNT(*) FROM messages m WHERE m.product_id = p.id) AS message_count
FROM products p
JOIN users u ON u.id = p.seller_id
"""


def _favorite_ids(db: Database, user_id: int | None, product_ids: list[int]) -> set[int]:
    if not user_id or not product_ids:
        return set()
    placeholders = ",".join("?" for _ in product_ids)
    rows = db.fetch_all(
        f"SELECT product_id FROM favorites WHERE user_id = ? AND product_id IN ({placeholders})",
        (user_id, *product_ids),
    )
    return {int(row["product_id"]) for row in rows}


def _one_product(db: Database, product_id: int, viewer_id: int | None = None) -> dict[str, Any]:
    row = db.fetch_one(PRODUCT_SELECT + " WHERE p.id = ?", (product_id,))
    if row is None:
        raise ApiError(404, "商品不存在", "PRODUCT_NOT_FOUND")
    data = dict(row)
    data["is_favorited"] = product_id in _favorite_ids(db, viewer_id, [product_id])
    return data


def _ensure_product_visible(row: dict[str, Any]) -> None:
    if row.get("is_deleted") or row.get("status") == "已下架":
        raise ApiError(404, "商品不存在或已下架", "PRODUCT_NOT_FOUND")


def _open_order(db: Database, product_id: int) -> dict[str, Any] | None:
    row = db.fetch_one(
        "SELECT id, status FROM orders WHERE product_id = ? AND status IN ('待确认', '已确认')",
        (product_id,),
    )
    return dict(row) if row else None


@router.get("/products/categories")
def list_categories(db: Annotated[Database, Depends(get_db)]):
    rows = db.fetch_all(
        """
        SELECT category, COUNT(*) AS count
        FROM products
        WHERE is_deleted = 0 AND status != '已下架'
        GROUP BY category
        ORDER BY count DESC, category ASC
        """
    )
    counts = {row["category"]: int(row["count"]) for row in rows}
    items = [
        {"name": category, "count": counts.get(category, 0)}
        for category in PRODUCT_CATEGORIES
    ]
    return ok({"items": items, "campuses": ["主校区", "东校区", "西校区", "南校区", "北校区"]})


@router.get("/products")
def list_products(
    db: Annotated[Database, Depends(get_db)],
    user: OptionalUser,
    q: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None, max_length=30),
    min_price: Decimal | None = Query(default=None, ge=0, le=Decimal("999999.99")),
    max_price: Decimal | None = Query(default=None, ge=0, le=Decimal("999999.99")),
    campus: str | None = Query(default=None, max_length=50),
    status: str | None = Query(default=None, max_length=10),
    sort: str = Query(default="newest", max_length=20),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ApiError(422, "最低价格不能高于最高价格", "INVALID_PRICE_RANGE")
    if status is not None and status not in ("在售", "已预订", "已售出"):
        raise ApiError(422, "商品状态筛选不合法", "INVALID_STATUS")
    if category is not None and category not in PRODUCT_CATEGORIES:
        raise ApiError(422, "商品分类不合法", "INVALID_CATEGORY")

    sort_options = {
        "newest": "p.created_at DESC, p.id DESC",
        "oldest": "p.created_at ASC, p.id ASC",
        "price_asc": "CAST(p.price AS REAL) ASC, p.id DESC",
        "price_desc": "CAST(p.price AS REAL) DESC, p.id DESC",
    }
    if sort not in sort_options:
        raise ApiError(422, "排序方式不合法", "INVALID_SORT")

    conditions = ["p.is_deleted = 0", "p.status != '已下架'"]
    params: list[Any] = []
    if q:
        keyword = f"%{q.strip()}%"
        conditions.append("(p.name LIKE ? OR p.description LIKE ? OR p.category LIKE ?)")
        params.extend([keyword, keyword, keyword])
    if category:
        conditions.append("p.category = ?")
        params.append(category)
    if min_price is not None:
        conditions.append("CAST(p.price AS REAL) >= ?")
        params.append(float(min_price))
    if max_price is not None:
        conditions.append("CAST(p.price AS REAL) <= ?")
        params.append(float(max_price))
    if campus:
        conditions.append("p.campus = ?")
        params.append(campus)
    if status:
        conditions.append("p.status = ?")
        params.append(status)
    where = " WHERE " + " AND ".join(conditions)

    total_row = db.fetch_one("SELECT COUNT(*) AS total FROM products p" + where, tuple(params))
    total = int(total_row["total"]) if total_row else 0
    offset = (page - 1) * page_size
    rows = db.fetch_all(
        PRODUCT_SELECT + where + f" ORDER BY {sort_options[sort]} LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )
    rows_dict = [dict(row) for row in rows]
    favorites = _favorite_ids(db, int(user["id"]) if user else None, [int(r["id"]) for r in rows_dict])
    items = []
    for row in rows_dict:
        row["is_favorited"] = int(row["id"]) in favorites
        items.append(product_data(row))
    return ok({"items": items, "pagination": pagination(page, page_size, total)})


@router.post("/products", status_code=201)
def create_product(
    payload: ProductCreateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    now = iso_now()
    product_id = db.execute(
        """
        INSERT INTO products
            (seller_id, name, description, price, category, image_url, campus,
             status, moderation_note, is_deleted, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, '在售', '', 0, ?, ?)
        """,
        (
            user["id"],
            payload.name,
            payload.description,
            money_text(payload.price),
            payload.category,
            payload.image_url,
            payload.campus,
            now,
            now,
        ),
    )
    return ok(product_data(_one_product(db, product_id, int(user["id"]))), "商品发布成功", 201)


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Annotated[Database, Depends(get_db)],
    user: OptionalUser,
):
    row = _one_product(db, product_id, int(user["id"]) if user else None)
    _ensure_product_visible(row)
    return ok(product_data(row))


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    row = _one_product(db, product_id, int(user["id"]))
    _ensure_product_visible(row)
    if int(row["seller_id"]) != int(user["id"]):
        raise ApiError(403, "只能编辑自己发布的商品", "FORBIDDEN")

    changes = {key: value for key, value in payload.model_dump(exclude_unset=True).items() if value is not None}
    if not changes:
        raise ApiError(422, "没有可更新的字段", "NO_CHANGES")
    if row["status"] == "已下架" and changes.get("status") == "在售":
        raise ApiError(403, "已下架商品只能由管理员恢复", "FORBIDDEN")

    open_order = _open_order(db, product_id)
    if open_order and ("status" in changes or "price" in changes):
        raise ApiError(409, "商品存在进行中的订单，暂不能修改价格或状态", "ACTIVE_ORDER_EXISTS")

    if "price" in changes:
        changes["price"] = money_text(changes["price"])
    changes["updated_at"] = iso_now()
    assignments = ", ".join(f"{field} = ?" for field in changes)
    db.execute(
        f"UPDATE products SET {assignments} WHERE id = ?",
        tuple(changes.values()) + (product_id,),
    )
    return ok(product_data(_one_product(db, product_id, int(user["id"]))), "商品已更新")


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    row = _one_product(db, product_id, int(user["id"]))
    _ensure_product_visible(row)
    if int(row["seller_id"]) != int(user["id"]):
        raise ApiError(403, "只能删除自己发布的商品", "FORBIDDEN")
    if _open_order(db, product_id):
        raise ApiError(409, "商品存在进行中的订单，暂不能删除", "ACTIVE_ORDER_EXISTS")
    db.execute(
        "UPDATE products SET is_deleted = 1, status = '已下架', updated_at = ? WHERE id = ?",
        (iso_now(), product_id),
    )
    return ok(None, "商品已删除")


@router.post("/products/{product_id}/favorite")
def add_favorite(
    product_id: int,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    row = _one_product(db, product_id, int(user["id"]))
    _ensure_product_visible(row)
    try:
        db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, product_id, created_at) VALUES (?, ?, ?)",
            (user["id"], product_id, iso_now()),
        )
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "收藏失败，请稍后重试", "FAVORITE_FAILED") from exc
    count = db.fetch_one("SELECT COUNT(*) AS count FROM favorites WHERE product_id = ?", (product_id,))
    return ok({"is_favorited": True, "favorite_count": int(count["count"])}, "已收藏")


@router.delete("/products/{product_id}/favorite")
def remove_favorite(
    product_id: int,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    db.execute("DELETE FROM favorites WHERE user_id = ? AND product_id = ?", (user["id"], product_id))
    count = db.fetch_one("SELECT COUNT(*) AS count FROM favorites WHERE product_id = ?", (product_id,))
    return ok({"is_favorited": False, "favorite_count": int(count["count"])}, "已取消收藏")


@router.get("/products/{product_id}/messages")
def list_messages(
    product_id: int,
    db: Annotated[Database, Depends(get_db)],
    user: OptionalUser,
):
    product = _one_product(db, product_id)
    _ensure_product_visible(product)
    rows = db.fetch_all(
        """
        SELECT m.*, u.username AS author_username,
               u.display_name AS author_display_name,
               u.avatar_url AS author_avatar_url
        FROM messages m
        JOIN users u ON u.id = m.user_id
        WHERE m.product_id = ?
        ORDER BY m.created_at DESC, m.id DESC
        """,
        (product_id,),
    )
    viewer_id = int(user["id"]) if user else None
    is_admin = bool(user and user["role"] == "admin")
    items = []
    for row in rows:
        data = dict(row)
        data["can_delete"] = is_admin or viewer_id == int(data["user_id"])
        items.append(message_data(data))
    return ok({"items": items, "total": len(items)})


@router.post("/products/{product_id}/messages", status_code=201)
def create_message(
    product_id: int,
    payload: MessageCreateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    product = _one_product(db, product_id, int(user["id"]))
    _ensure_product_visible(product)
    message_id = db.execute(
        "INSERT INTO messages (product_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
        (product_id, user["id"], payload.content, iso_now()),
    )
    row = db.fetch_one(
        """
        SELECT m.*, u.username AS author_username,
               u.display_name AS author_display_name,
               u.avatar_url AS author_avatar_url
        FROM messages m JOIN users u ON u.id = m.user_id
        WHERE m.id = ?
        """,
        (message_id,),
    )
    data = dict(row)
    data["can_delete"] = True
    return ok(message_data(data), "留言成功", 201)


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    row = db.fetch_one("SELECT * FROM messages WHERE id = ?", (message_id,))
    if row is None:
        raise ApiError(404, "留言不存在", "MESSAGE_NOT_FOUND")
    if int(row["user_id"]) != int(user["id"]) and user["role"] != "admin":
        raise ApiError(403, "不能删除他人的留言", "FORBIDDEN")
    db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    return ok(None, "留言已删除")
