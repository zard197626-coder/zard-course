"""FastAPI 应用入口：校园二手交易平台。"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import hash_password
from .database import Database, iso_now, resolve_database_path
from .models import PRODUCT_CATEGORIES
from .responses import ApiError, error_response, ok
from .routers import admin, auth, orders, products, users

logger = logging.getLogger("campus_market")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _bootstrap_admin(db: Database) -> None:
    """可选：通过环境变量创建初始管理员，不在代码中保存任何默认密码。"""
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        return
    existing = db.fetch_one("SELECT id, role FROM users WHERE username = ? COLLATE NOCASE", (username,))
    if existing is not None:
        if existing["role"] != "admin":
            logger.warning("ADMIN_USERNAME 已存在但不是管理员，未自动提权")
        return
    email = os.getenv("ADMIN_EMAIL", "admin@campus.local").strip()
    if db.fetch_one("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (email,)):
        logger.warning("ADMIN_EMAIL 已被使用，跳过管理员初始化")
        return
    db.execute(
        """
        INSERT INTO users
            (username, email, password_hash, display_name, is_student, role,
             campus, bio, avatar_url, is_active, created_at)
        VALUES (?, ?, ?, '平台管理员', 0, 'admin', '主校区', '', '', 1, ?)
        """,
        (username, email, hash_password(password), iso_now()),
    )
    logger.info("已根据环境变量创建管理员账号：%s", username)


def create_app(database_path: str | os.PathLike[str] | None = None) -> FastAPI:
    db = Database(database_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        db.init_schema()
        _bootstrap_admin(db)
        application.state.db = db
        yield

    application = FastAPI(
        title="校园二手交易平台 API",
        description="面向校园的二手商品交易平台，包含用户、商品、收藏、留言、订单和管理员功能。",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.db = db

    origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return error_response(exc.status_code, exc.message, exc.code, exc.details)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])),
                "message": error.get("msg", "输入不合法"),
            }
            for error in exc.errors()
        ]
        return error_response(422, "输入数据校验失败", "VALIDATION_ERROR", details)

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return error_response(exc.status_code, str(exc.detail), code)

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("未处理的服务器错误：%s %s", request.method, request.url.path)
        return error_response(500, "服务器内部错误，请稍后重试", "INTERNAL_ERROR")

    @application.get("/api/health", tags=["系统"])
    def health():
        return ok({"status": "ok", "service": "campus-market", "version": "1.0.0"})

    @application.get("/api/overview", tags=["系统"])
    def overview():
        counts = db.fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM users WHERE is_active = 1) AS users,
                (SELECT COUNT(*) FROM products WHERE is_deleted = 0 AND status = '在售') AS products,
                (SELECT COUNT(*) FROM orders WHERE status = '已完成') AS completed_orders,
                (SELECT COUNT(*) FROM products WHERE is_deleted = 0 AND status != '已下架') AS total_products
            """
        )
        categories = db.fetch_all(
            """
            SELECT category, COUNT(*) AS count FROM products
            WHERE is_deleted = 0 AND status != '已下架'
            GROUP BY category ORDER BY count DESC, category ASC
            """
        )
        return ok(
            {
                "users": int(counts["users"] or 0) if counts else 0,
                "on_sale": int(counts["products"] or 0) if counts else 0,
                "completed_orders": int(counts["completed_orders"] or 0) if counts else 0,
                "products": int(counts["total_products"] or 0) if counts else 0,
                "categories": [
                    {"name": row["category"], "count": int(row["count"])}
                    for row in categories
                ],
                "all_categories": list(PRODUCT_CATEGORIES),
            }
        )

    application.include_router(auth.router)
    application.include_router(products.router)
    application.include_router(orders.router)
    application.include_router(users.router)
    application.include_router(admin.router)

    if FRONTEND_DIR.is_dir():
        application.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return application


app = create_app()
