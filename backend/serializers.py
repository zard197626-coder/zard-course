"""数据库行到 API JSON 的统一序列化。"""

from __future__ import annotations

from typing import Any

from .models import PAYMENT_METHODS
from .money import as_money, money_text


def bool_value(value: Any) -> bool:
    return bool(value)


def public_user(row: dict[str, Any] | Any) -> dict[str, Any]:
    data = dict(row)
    return {
        "id": data["id"],
        "username": data["username"],
        "display_name": data.get("display_name") or data["username"],
        "email": data.get("email"),
        "is_student": bool(data.get("is_student")),
        "role": data.get("role", "user"),
        "campus": data.get("campus", ""),
        "bio": data.get("bio", ""),
        "avatar_url": data.get("avatar_url", ""),
        "is_active": bool(data.get("is_active", 1)),
        "created_at": data.get("created_at"),
    }


def seller_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["seller_id"],
        "username": row.get("seller_username", ""),
        "display_name": row.get("seller_display_name") or row.get("seller_username", ""),
        "avatar_url": row.get("seller_avatar_url", ""),
        "campus": row.get("seller_campus", ""),
        "is_student": bool(row.get("seller_is_student")),
    }


def product_data(row: dict[str, Any], *, include_description: bool = True) -> dict[str, Any]:
    data = {
        "id": row["id"],
        "name": row["name"],
        "price": money_text(row["price"]),
        "category": row["category"],
        "image_url": row.get("image_url", ""),
        "campus": row.get("campus", ""),
        "status": row["status"],
        "seller": seller_summary(row),
        "favorite_count": int(row.get("favorite_count") or 0),
        "message_count": int(row.get("message_count") or 0),
        "is_favorited": bool(row.get("is_favorited") or 0),
        "is_deleted": bool(row.get("is_deleted") or 0),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }
    if include_description:
        data["description"] = row.get("description", "")
        data["moderation_note"] = row.get("moderation_note", "")
    return data


def payment_method_label(method: str) -> str:
    if method == "mock_legacy":
        return "历史模拟支付（已迁移）"
    return PAYMENT_METHODS.get(method, "模拟支付")


def order_data(row: dict[str, Any]) -> dict[str, Any]:
    payment_status = row.get("payment_status") or "未支付"
    payment_method = row.get("payment_method") or ""
    return {
        "id": row["id"],
        "status": row["status"],
        "original_price": money_text(row["original_price"]),
        "discount_amount": money_text(row["discount_amount"]),
        "final_price": money_text(row["final_price"]),
        "student_discount": bool(row.get("student_discount")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "product": {
            "id": row["product_id"],
            "name": row.get("product_name", ""),
            "image_url": row.get("product_image_url", ""),
            "price": money_text(row.get("product_price") or row["original_price"]),
            "status": row.get("product_status", ""),
            "status_deleted": bool(row.get("product_is_deleted") or 0),
            "campus": row.get("product_campus", ""),
        },
        "buyer": {
            "id": row["buyer_id"],
            "username": row.get("buyer_username", ""),
            "display_name": row.get("buyer_display_name") or row.get("buyer_username", ""),
            "avatar_url": row.get("buyer_avatar_url", ""),
        },
        "seller": {
            "id": row["seller_id"],
            "username": row.get("seller_username", ""),
            "display_name": row.get("seller_display_name") or row.get("seller_username", ""),
            "avatar_url": row.get("seller_avatar_url", ""),
        },
        "payment": {
            "status": payment_status,
            "method": payment_method,
            "method_label": payment_method_label(payment_method) if payment_method else "",
            "transaction_no": row.get("payment_no") or "",
            "paid_at": row.get("paid_at"),
            "refunded_at": row.get("refunded_at"),
            "refund_amount": money_text(row.get("refund_amount") or "0.00"),
        },
    }


def payment_data(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "order_id": row["order_id"],
        "amount": money_text(row["amount"]),
        "method": row["method"],
        "method_label": payment_method_label(row["method"]),
        "status": row["status"],
        "transaction_no": row["transaction_no"],
        "failure_reason": row.get("failure_reason", ""),
        "created_at": row.get("created_at"),
        "paid_at": row.get("paid_at"),
        "refunded_at": row.get("refunded_at"),
    }


def message_data(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "product_id": row["product_id"],
        "content": row["content"],
        "created_at": row["created_at"],
        "author": {
            "id": row["user_id"],
            "username": row.get("author_username", ""),
            "display_name": row.get("author_display_name") or row.get("author_username", ""),
            "avatar_url": row.get("author_avatar_url", ""),
        },
        "can_delete": bool(row.get("can_delete") or 0),
    }


def pagination(page: int, page_size: int, total: int) -> dict[str, int]:
    pages = (total + page_size - 1) // page_size if total else 0
    return {"page": page, "page_size": page_size, "total": total, "pages": pages}


def decimal_sum(values: list[str]) -> str:
    total = sum((as_money(value) for value in values), as_money("0"))
    return money_text(total)
