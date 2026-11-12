"""管理员统计、用户管理与商品下架。"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from ..auth import AdminUser
from ..database import Database, iso_now
from ..deps import get_db
from ..models import ORDER_STATUSES, PRODUCT_CATEGORIES, PRODUCT_STATUSES
from ..money import as_money, money_text
from ..responses import ApiError, ok
from ..schemas import AdminUserUpdateRequest, TakedownRequest
from ..serializers import decimal_sum, order_data, pagination, product_data, public_user
from .orders import ORDER_SELECT
from .products import PRODUCT_SELECT, _one_product

router = APIRouter(prefix="/api/admin", tags=["管理员"])


@router.get("/statistics")
def statistics(
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
):
    users = db.fetch_one(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active FROM users"
    )
    products = db.fetch_one(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = '在售' AND is_deleted = 0 THEN 1 ELSE 0 END) AS on_sale,
               SUM(CASE WHEN is_deleted = 1 THEN 1 ELSE 0 END) AS deleted
        FROM products
        """
    )
    orders = db.fetch_one("SELECT COUNT(*) AS total FROM orders")
    status_rows = db.fetch_all("SELECT status, COUNT(*) AS count FROM orders GROUP BY status")
    order_status = {status: 0 for status in ORDER_STATUSES}
    for row in status_rows:
        order_status[row["status"]] = int(row["count"])
    completed_prices = db.fetch_all("SELECT final_price FROM orders WHERE status = '已完成'")
    total_sales = decimal_sum([row["final_price"] for row in completed_prices])
    completed_count = max(1, order_status["已完成"])
    average_order = money_text(as_money(total_sales) / completed_count)
    category_rows = db.fetch_all(
        """
        SELECT category, COUNT(*) AS count FROM products
        WHERE is_deleted = 0 AND status != '已下架'
        GROUP BY category
        """
    )
    category_counts = {row["category"]: int(row["count"]) for row in category_rows}
    recent_rows = db.fetch_all(
        ORDER_SELECT + " ORDER BY o.created_at DESC, o.id DESC LIMIT 5"
    )
    return ok(
        {
            "users": {
                "total": int(users["total"] or 0),
                "active": int(users["active"] or 0),
            },
            "products": {
                "total": int(products["total"] or 0),
                "on_sale": int(products["on_sale"] or 0),
                "deleted": int(products["deleted"] or 0),
            },
            "orders": {
                "total": int(orders["total"] or 0),
                "by_status": order_status,
            },
            "sales_amount": total_sales,
            "average_completed_order": average_order,
            "categories": [
                {"name": category, "count": category_counts.get(category, 0)}
                for category in PRODUCT_CATEGORIES
            ],
            "recent_orders": [order_data(dict(row)) for row in recent_rows],
        }
    )


@router.get("/users")
def list_users(
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
    q: str | None = Query(default=None, max_length=80),
    role: str | None = Query(default=None, pattern="^(user|admin)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    conditions: list[str] = []
    params: list[Any] = []
    if q:
        keyword = f"%{q.strip()}%"
        conditions.append("(username LIKE ? OR email LIKE ? OR display_name LIKE ?)")
        params.extend([keyword, keyword, keyword])
    if role:
        conditions.append("role = ?")
        params.append(role)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total_row = db.fetch_one("SELECT COUNT(*) AS total FROM users" + where, tuple(params))
    total = int(total_row["total"]) if total_row else 0
    rows = db.fetch_all(
        """
        SELECT u.*,
               (SELECT COUNT(*) FROM products p WHERE p.seller_id = u.id AND p.is_deleted = 0) AS product_count,
               (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.id) AS purchase_count,
               (SELECT COUNT(*) FROM orders o WHERE o.seller_id = u.id) AS sale_count
        FROM users u
        """
        + where
        + " ORDER BY u.created_at DESC, u.id DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = []
    for row in rows:
        data = public_user(row)
        data["product_count"] = int(row["product_count"])
        data["purchase_count"] = int(row["purchase_count"])
        data["sale_count"] = int(row["sale_count"])
        items.append(data)
    return ok({"items": items, "pagination": pagination(page, page_size, total)})


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
):
    target = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if target is None:
        raise ApiError(404, "用户不存在", "USER_NOT_FOUND")
    if int(admin["id"]) == user_id:
        raise ApiError(400, "不能修改自己的管理员状态或角色", "CANNOT_MODIFY_SELF")
    if target["role"] == "admin" and payload.role == "user":
        admin_count = db.fetch_one("SELECT COUNT(*) AS count FROM users WHERE role = 'admin' AND is_active = 1")
        if admin_count and int(admin_count["count"]) <= 1:
            raise ApiError(409, "不能降级最后一个管理员", "LAST_ADMIN")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise ApiError(422, "没有可更新的字段", "NO_CHANGES")
    if "is_active" in changes:
        changes["is_active"] = int(bool(changes["is_active"]))
    assignments = ", ".join(f"{field} = ?" for field in changes)
    db.execute(
        f"UPDATE users SET {assignments} WHERE id = ?",
        tuple(changes.values()) + (user_id,),
    )
    if changes.get("is_active") == 0:
        db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    updated = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return ok(public_user(updated), "用户信息已更新")


@router.get("/products")
def list_all_products(
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
    q: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None),
    include_deleted: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if status is not None and status not in PRODUCT_STATUSES:
        raise ApiError(422, "商品状态不合法", "INVALID_STATUS")
    conditions: list[str] = []
    params: list[Any] = []
    if not include_deleted:
        conditions.append("p.is_deleted = 0")
    if q:
        keyword = f"%{q.strip()}%"
        conditions.append("(p.name LIKE ? OR p.description LIKE ?)")
        params.extend([keyword, keyword])
    if status:
        conditions.append("p.status = ?")
        params.append(status)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total_row = db.fetch_one("SELECT COUNT(*) AS total FROM products p" + where, tuple(params))
    total = int(total_row["total"]) if total_row else 0
    rows = db.fetch_all(
        PRODUCT_SELECT + where + " ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    return ok(
        {
            "items": [product_data(dict(row)) for row in rows],
            "pagination": pagination(page, page_size, total),
        }
    )


@router.put("/products/{product_id}/takedown")
def takedown_product(
    product_id: int,
    payload: TakedownRequest,
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
):
    product = _one_product(db, product_id)
    db.execute(
        "UPDATE products SET status = '已下架', moderation_note = ?, updated_at = ? WHERE id = ?",
        (payload.reason, iso_now(), product_id),
    )
    return ok(product_data(_one_product(db, product_id)), "商品已下架")


@router.put("/products/{product_id}/restore")
def restore_product(
    product_id: int,
    admin: AdminUser,
    db: Annotated[Database, Depends(get_db)],
):
    product = _one_product(db, product_id)
    if product["is_deleted"]:
        raise ApiError(409, "已删除商品不能恢复，请让卖家重新发布", "PRODUCT_DELETED")
    open_order = db.fetch_one(
        "SELECT id FROM orders WHERE product_id = ? AND status IN ('待确认', '已确认')",
        (product_id,),
    )
    new_status = "已预订" if open_order else "在售"
    db.execute(
        "UPDATE products SET status = ?, moderation_note = '', updated_at = ? WHERE id = ?",
        (new_status, iso_now(), product_id),
    )
    return ok(product_data(_one_product(db, product_id)), "商品已恢复上架")
