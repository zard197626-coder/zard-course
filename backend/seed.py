"""初始化数据库并写入测试用种子数据。

用法：
    python -m backend.seed
    python -m backend.seed --reset
    python -m backend.seed --admin-password "自定义强密码"

脚本不会把密码写入文件或数据库明文字段；未提供密码时会随机生成并仅在终端打印一次。
"""

from __future__ import annotations

import argparse
import os
import secrets
from typing import Any

from .auth import hash_password
from .database import Database, iso_now
from .money import money_text, price_breakdown
from .models import PRODUCT_CATEGORIES


DEMO_PRODUCTS = [
    {
        "name": "高等数学（同济第七版）上下册",
        "description": "教材有少量笔记，无缺页，适合期末复习。可在主校区图书馆当面交易。",
        "price": "32.00",
        "category": "教材书籍",
        "campus": "主校区",
        "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=900&q=80",
    },
    {
        "name": "罗技 M330 静音无线鼠标",
        "description": "使用约三个月，功能正常，附原装接收器。宿舍楼下自提。",
        "price": "79.90",
        "category": "电子数码",
        "campus": "东校区",
        "image": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=900&q=80",
    },
    {
        "name": "宿舍折叠小书桌",
        "description": "白色折叠桌，桌面 60×40cm，可放笔记本电脑，搬宿舍不方便带走。",
        "price": "45.00",
        "category": "生活用品",
        "campus": "西校区",
        "image": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=900&q=80",
    },
    {
        "name": "羽毛球拍双拍套装",
        "description": "碳素双拍，含拍套和三个训练球，适合入门。周末可约球。",
        "price": "88.00",
        "category": "运动户外",
        "campus": "南校区",
        "image": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=900&q=80",
    },
    {
        "name": "学院风双肩包",
        "description": "深蓝色，可装 15 寸电脑，九成新，拉链顺滑。",
        "price": "59.00",
        "category": "服饰鞋包",
        "campus": "北校区",
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&q=80",
    },
    {
        "name": "大学英语六级真题集",
        "description": "近五年真题，答案完整，听力音频二维码可用。",
        "price": "18.50",
        "category": "教材书籍",
        "campus": "主校区",
        "image": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=900&q=80",
    },
    {
        "name": "小米移动电源 10000mAh",
        "description": "容量正常，外观有轻微使用痕迹，送短数据线。",
        "price": "39.00",
        "category": "电子数码",
        "campus": "东校区",
        "image": "https://images.unsplash.com/photo-1609592806596-b43bada2f4be?w=900&q=80",
    },
    {
        "name": "桌面护眼台灯",
        "description": "三档色温，USB 供电，宿舍书桌适用。",
        "price": "28.00",
        "category": "生活用品",
        "campus": "西校区",
        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=900&q=80",
    },
]


def _find_user(db: Database, username: str) -> dict[str, Any] | None:
    row = db.fetch_one("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,))
    return dict(row) if row else None


def _create_user(
    db: Database,
    username: str,
    email: str,
    password: str,
    display_name: str,
    is_student: bool,
    role: str = "user",
    campus: str = "主校区",
    bio: str = "",
) -> tuple[dict[str, Any], bool]:
    existing = _find_user(db, username)
    if existing:
        return existing, False
    user_id = db.execute(
        """
        INSERT INTO users
            (username, email, password_hash, display_name, is_student, role,
             campus, bio, avatar_url, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', 1, ?)
        """,
        (
            username,
            email,
            hash_password(password),
            display_name,
            int(is_student),
            role,
            campus,
            bio,
            iso_now(),
        ),
    )
    row = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return dict(row), True


def seed(database_path: str | None = None, reset: bool = False, admin_password: str | None = None) -> None:
    db = Database(database_path)
    if reset:
        db.reset_schema()
    else:
        db.init_schema()

    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
    generated_admin_password = admin_password or os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
    admin, admin_created = _create_user(
        db,
        admin_username,
        os.getenv("ADMIN_EMAIL", "admin@campus.local"),
        generated_admin_password,
        "平台管理员",
        False,
        role="admin",
        bio="负责校园二手平台的日常运营与内容审核。",
    )

    demo_password = os.getenv("DEMO_PASSWORD") or secrets.token_urlsafe(10)
    seller, seller_created = _create_user(
        db,
        "campus_seller",
        "seller@campus.local",
        demo_password,
        "阿哲学长",
        True,
        campus="主校区",
        bio="毕业清仓，价格好商量，支持校内自提。",
    )
    buyer, buyer_created = _create_user(
        db,
        "campus_buyer",
        "buyer@campus.local",
        demo_password,
        "小满同学",
        True,
        campus="东校区",
        bio="正在给宿舍添置一些实用好物。",
    )
    visitor, visitor_created = _create_user(
        db,
        "campus_visitor",
        "visitor@campus.local",
        demo_password,
        "林老师",
        False,
        campus="西校区",
        bio="非学生用户，按原价购买。",
    )

    existing_products = db.fetch_one("SELECT COUNT(*) AS count FROM products")
    created_products = 0
    if not existing_products or int(existing_products["count"]) == 0:
        for index, item in enumerate(DEMO_PRODUCTS):
            db.execute(
                """
                INSERT INTO products
                    (seller_id, name, description, price, category, image_url, campus,
                     status, moderation_note, is_deleted, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, '在售', '', 0, ?, ?)
                """,
                (
                    seller["id"],
                    item["name"],
                    item["description"],
                    item["price"],
                    item["category"],
                    item["image"],
                    item["campus"],
                    iso_now(),
                    iso_now(),
                ),
            )
            created_products += 1
        first_product = db.fetch_one("SELECT * FROM products ORDER BY id ASC LIMIT 1")
        if first_product:
            db.execute(
                "INSERT OR IGNORE INTO favorites (user_id, product_id, created_at) VALUES (?, ?, ?)",
                (buyer["id"], first_product["id"], iso_now()),
            )
            db.execute(
                "INSERT INTO messages (product_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                (first_product["id"], buyer["id"], "请问教材还有吗？周三下午方便在图书馆门口交易吗？", iso_now()),
            )
            db.execute(
                "INSERT INTO messages (product_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                (first_product["id"], seller["id"], "还在的，周三下午三点可以，到了给我留言。", iso_now()),
            )

        sold_product = db.fetch_one("SELECT * FROM products WHERE category = '电子数码' ORDER BY id DESC LIMIT 1")
        if sold_product:
            breakdown = price_breakdown(sold_product["price"], True)
            now = iso_now()
            with db.transaction() as connection:
                connection.execute(
                    "UPDATE products SET status = '已售出', updated_at = ? WHERE id = ?",
                    (now, sold_product["id"]),
                )
                connection.execute(
                    """
                    INSERT INTO orders
                        (product_id, buyer_id, seller_id, status, original_price,
                         discount_amount, final_price, student_discount, created_at, updated_at)
                    VALUES (?, ?, ?, '已完成', ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        sold_product["id"],
                        buyer["id"],
                        seller["id"],
                        money_text(breakdown["original_price"]),
                        money_text(breakdown["discount_amount"]),
                        money_text(breakdown["final_price"]),
                        now,
                        now,
                    ),
                )

    print("数据库初始化完成：", db.path)
    print(
        f"用户：管理员 {admin_username}，普通用户 campus_seller / campus_buyer / campus_visitor"
    )
    if admin_created:
        print(f"管理员初始密码（仅本次显示）：{generated_admin_password}")
    else:
        print("管理员已存在，未重置密码。")
    if any((seller_created, buyer_created, visitor_created)):
        print(f"演示账号密码（仅本次显示）：{demo_password}")
    else:
        print("演示账号已存在，未重置密码。")
    if created_products:
        print(f"已写入 {created_products} 件演示商品，并生成收藏、留言和一条已完成订单。")
    else:
        print("商品数据已存在，未重复写入。")


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化校园二手交易平台数据库")
    parser.add_argument("--reset", action="store_true", help="删除现有表并重建（会丢失数据）")
    parser.add_argument("--admin-password", help="管理员密码；不传则随机生成")
    args = parser.parse_args()
    seed(reset=args.reset, admin_password=args.admin_password)


if __name__ == "__main__":
    main()
