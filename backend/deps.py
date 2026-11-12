"""FastAPI 通用依赖。"""

from fastapi import Request

from .database import Database


def get_db(request: Request) -> Database:
    return request.app.state.db
