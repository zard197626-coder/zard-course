"""数据库表结构与领域常量。"""

PRODUCT_STATUSES = ("在售", "已预订", "已售出", "已下架")
PRODUCT_CATEGORIES = (
    "教材书籍",
    "电子数码",
    "生活用品",
    "运动户外",
    "服饰鞋包",
    "美妆个护",
    "票券卡券",
    "其他",
)
ORDER_STATUSES = ("待确认", "已确认", "已完成", "已取消")
ACTIVE_ORDER_STATUSES = ("待确认", "已确认", "已完成")
PAYMENT_STATUSES = ("未支付", "已支付", "已退款")
PAYMENT_RECORD_STATUSES = ("成功", "失败", "已退款")
PAYMENT_METHODS = {
    "mock_campus": "校园卡（模拟）",
    "mock_card": "银行卡（模拟）",
    "mock_wallet": "校园钱包（模拟）",
}
CAMPUSES = ("主校区", "东校区", "西校区", "南校区", "北校区")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_student INTEGER NOT NULL DEFAULT 1 CHECK (is_student IN (0, 1)),
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    campus TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price TEXT NOT NULL,
    category TEXT NOT NULL,
    image_url TEXT NOT NULL DEFAULT '',
    campus TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '在售'
        CHECK (status IN ('在售', '已预订', '已售出', '已下架')),
    moderation_note TEXT NOT NULL DEFAULT '',
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT '待确认'
        CHECK (status IN ('待确认', '已确认', '已完成', '已取消')),
    original_price TEXT NOT NULL,
    discount_amount TEXT NOT NULL,
    final_price TEXT NOT NULL,
    student_discount INTEGER NOT NULL DEFAULT 0 CHECK (student_discount IN (0, 1)),
    payment_status TEXT NOT NULL DEFAULT '未支付'
        CHECK (payment_status IN ('未支付', '已支付', '已退款')),
    payment_method TEXT NOT NULL DEFAULT '',
    payment_no TEXT NOT NULL DEFAULT '',
    paid_at TEXT,
    refunded_at TEXT,
    refund_amount TEXT NOT NULL DEFAULT '0.00',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount TEXT NOT NULL,
    method TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('成功', '失败', '已退款')),
    transaction_no TEXT NOT NULL UNIQUE,
    failure_reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    paid_at TEXT,
    refunded_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_active_product
    ON orders(product_id)
    WHERE status IN ('待确认', '已确认', '已完成');

CREATE INDEX IF NOT EXISTS idx_products_status_created
    ON products(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_seller
    ON products(seller_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user
    ON favorites(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_product
    ON messages(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_buyer
    ON orders(buyer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_seller
    ON orders(seller_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_order
    ON payments(order_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_token
    ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_user
    ON sessions(user_id);
"""


def migrate_schema(connection) -> None:
    """为旧数据库补充模拟支付字段，并回填历史已确认/已完成订单。

    旧版本订单没有 payment_status 字段。直接 ALTER TABLE 可以保留原数据，
    并将已确认或已完成的订单视为历史模拟支付成功。
    """
    existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(orders)").fetchall()}
    additions = (
        ("payment_status", "TEXT NOT NULL DEFAULT '未支付'"),
        ("payment_method", "TEXT NOT NULL DEFAULT ''"),
        ("payment_no", "TEXT NOT NULL DEFAULT ''"),
        ("paid_at", "TEXT"),
        ("refunded_at", "TEXT"),
        ("refund_amount", "TEXT NOT NULL DEFAULT '0.00'"),
    )
    for column, definition in additions:
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")

    legacy_rows = connection.execute(
        """
        SELECT id, buyer_id, final_price, created_at, updated_at
        FROM orders
        WHERE payment_status = '未支付' AND status IN ('已确认', '已完成')
        """
    ).fetchall()
    for row in legacy_rows:
        payment_no = f"MOCK-LEGACY-{row['id']}"
        paid_at = row["updated_at"] or row["created_at"]
        connection.execute(
            """
            UPDATE orders
            SET payment_status = '已支付', payment_method = 'mock_legacy',
                payment_no = ?, paid_at = ?
            WHERE id = ?
            """,
            (payment_no, paid_at, row["id"]),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO payments
                (order_id, user_id, amount, method, status, transaction_no,
                 failure_reason, created_at, paid_at, refunded_at)
            VALUES (?, ?, ?, 'mock_legacy', '成功', ?, '', ?, ?, NULL)
            """,
            (row["id"], row["buyer_id"], row["final_price"], payment_no, paid_at, paid_at),
        )
    connection.commit()


def init_schema(connection) -> None:
    """在给定连接上创建全部表和索引（幂等），并执行轻量迁移。"""
    connection.executescript(SCHEMA_SQL)
    migrate_schema(connection)
    connection.commit()
