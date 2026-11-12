"""订单创建、查询和状态流转。"""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from ..auth import CurrentUser
from ..database import Database, iso_now
from ..deps import get_db
from ..models import ORDER_STATUSES
from ..money import money_text, price_breakdown
from ..responses import ApiError, ok
from ..schemas import OrderCreateRequest, OrderStatusUpdateRequest
from ..serializers import order_data, pagination

router = APIRouter(prefix="/api/orders", tags=["订单"])

ORDER_SELECT = """
SELECT o.*,
       p.name AS product_name,
       p.image_url AS product_image_url,
       p.price AS product_price,
       p.status AS product_status,
       p.campus AS product_campus,
       p.is_deleted AS product_is_deleted,
       buyer.username AS buyer_username,
       buyer.display_name AS buyer_display_name,
       buyer.avatar_url AS buyer_avatar_url,
       seller.username AS seller_username,
       seller.display_name AS seller_display_name,
       seller.avatar_url AS seller_avatar_url
FROM orders o
JOIN products p ON p.id = o.product_id
JOIN users buyer ON buyer.id = o.buyer_id
JOIN users seller ON seller.id = o.seller_id
"""


def _fetch_order(db: Database, order_id: int) -> dict[str, Any]:
    row = db.fetch_one(ORDER_SELECT + " WHERE o.id = ?", (order_id,))
    if row is None:
        raise ApiError(404, "订单不存在", "ORDER_NOT_FOUND")
    return dict(row)


def _can_view(order: dict[str, Any], user: dict[str, Any]) -> bool:
    return user["role"] == "admin" or int(user["id"]) in (
        int(order["buyer_id"]),
        int(order["seller_id"]),
    )


def _transition_allowed(order: dict[str, Any], user: dict[str, Any], target: str) -> bool:
    current = str(order["status"])
    user_id = int(user["id"])
    is_buyer = user_id == int(order["buyer_id"])
    is_seller = user_id == int(order["seller_id"])
    is_admin = user["role"] == "admin"

    if current in ("已完成", "已取消") or current == target:
        return False
    if target == "已确认":
        return current == "待确认" and (is_seller or is_admin)
    if target == "已完成":
        return current == "已确认" and (is_buyer or is_seller or is_admin)
    if target == "已取消":
        return current in ("待确认", "已确认") and (is_buyer or is_seller or is_admin)
    return False


@router.post("", status_code=201)
def create_order(
    payload: OrderCreateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    product = db.fetch_one(
        """
        SELECT p.*, u.username AS seller_username
        FROM products p JOIN users u ON u.id = p.seller_id
        WHERE p.id = ?
        """,
        (payload.product_id,),
    )
    if product is None or product["is_deleted"] or product["status"] == "已下架":
        raise ApiError(404, "商品不存在或已下架", "PRODUCT_NOT_FOUND")
    if int(product["seller_id"]) == int(user["id"]):
        raise ApiError(400, "不能购买自己发布的商品", "CANNOT_BUY_OWN_PRODUCT")
    if product["status"] != "在售":
        raise ApiError(409, "商品当前不可购买", "PRODUCT_NOT_AVAILABLE")

    existing = db.fetch_one(
        "SELECT id FROM orders WHERE product_id = ? AND status IN ('待确认', '已确认', '已完成')",
        (payload.product_id,),
    )
    if existing:
        raise ApiError(409, "该商品已有有效订单，不能重复购买", "ALREADY_PURCHASED")

    breakdown = price_breakdown(product["price"], bool(user["is_student"]))
    now = iso_now()
    try:
        with db.transaction() as connection:
            updated = connection.execute(
                """
                UPDATE products
                SET status = '已预订', updated_at = ?
                WHERE id = ? AND status = '在售' AND is_deleted = 0
                """,
                (now, payload.product_id),
            )
            if updated.rowcount != 1:
                raise ApiError(409, "商品已被其他买家预订", "PRODUCT_RESERVED")
            cursor = connection.execute(
                """
                INSERT INTO orders
                    (product_id, buyer_id, seller_id, status, original_price,
                     discount_amount, final_price, student_discount, created_at, updated_at)
                VALUES (?, ?, ?, '待确认', ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.product_id,
                    user["id"],
                    product["seller_id"],
                    money_text(breakdown["original_price"]),
                    money_text(breakdown["discount_amount"]),
                    money_text(breakdown["final_price"]),
                    int(breakdown["student_discount"]),
                    now,
                    now,
                ),
            )
            order_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "该商品已被购买，不能重复下单", "ALREADY_PURCHASED") from exc

    return ok(order_data(_fetch_order(db, order_id)), "订单创建成功，等待卖家确认", 201)


@router.get("")
def list_orders(
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
    role: str = Query(default="all", pattern="^(all|buyer|seller)$"),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    if status is not None and status not in ORDER_STATUSES:
        raise ApiError(422, "订单状态筛选不合法", "INVALID_STATUS")
    conditions: list[str] = []
    params: list[Any] = []
    if role == "buyer":
        conditions.append("o.buyer_id = ?")
        params.append(user["id"])
    elif role == "seller":
        conditions.append("o.seller_id = ?")
        params.append(user["id"])
    else:
        conditions.append("(o.buyer_id = ? OR o.seller_id = ?)")
        params.extend([user["id"], user["id"]])
    if status:
        conditions.append("o.status = ?")
        params.append(status)
    where = " WHERE " + " AND ".join(conditions)
    total_row = db.fetch_one("SELECT COUNT(*) AS total FROM orders o" + where, tuple(params))
    total = int(total_row["total"]) if total_row else 0
    rows = db.fetch_all(
        ORDER_SELECT + where + " ORDER BY o.created_at DESC, o.id DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = []
    for row in rows:
        data = order_data(dict(row))
        data["viewer_role"] = (
            "buyer" if int(row["buyer_id"]) == int(user["id"]) else "seller"
        ) if int(user["id"]) in (int(row["buyer_id"]), int(row["seller_id"])) else "admin"
        items.append(data)
    return ok({"items": items, "pagination": pagination(page, page_size, total)})


@router.get("/{order_id}")
def get_order(
    order_id: int,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    order = _fetch_order(db, order_id)
    if not _can_view(order, user):
        raise ApiError(403, "无权查看该订单", "FORBIDDEN")
    return ok(order_data(order))


@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    user: CurrentUser,
    db: Annotated[Database, Depends(get_db)],
):
    order = _fetch_order(db, order_id)
    if not _can_view(order, user):
        raise ApiError(403, "无权操作该订单", "FORBIDDEN")
    if not _transition_allowed(order, user, payload.status):
        raise ApiError(409, f"不能将订单从“{order['status']}”变更为“{payload.status}”", "INVALID_TRANSITION")

    now = iso_now()
    try:
        with db.transaction() as connection:
            changed = connection.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ? AND status = ?",
                (payload.status, now, order_id, order["status"]),
            )
            if changed.rowcount != 1:
                raise ApiError(409, "订单状态已被其他操作更新，请刷新后重试", "ORDER_CONFLICT")
            if payload.status == "已完成":
                connection.execute(
                    "UPDATE products SET status = '已售出', updated_at = ? WHERE id = ?",
                    (now, order["product_id"]),
                )
            elif payload.status == "已取消":
                connection.execute(
                    """
                    UPDATE products SET status = '在售', updated_at = ?
                    WHERE id = ? AND is_deleted = 0 AND status = '已预订'
                      AND NOT EXISTS (
                          SELECT 1 FROM orders
                          WHERE product_id = ? AND status IN ('待确认', '已确认')
                      )
                    """,
                    (now, order["product_id"], order["product_id"]),
                )
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "订单状态更新冲突", "ORDER_CONFLICT") from exc

    return ok(order_data(_fetch_order(db, order_id)), f"订单状态已更新为{payload.status}")
