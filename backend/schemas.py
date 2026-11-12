"""请求数据模型与输入校验。"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import ORDER_STATUSES, PRODUCT_CATEGORIES, PRODUCT_STATUSES
from .money import as_money

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[^\s]{3,30}$")


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("密码至少需要 8 个字符")
    if len(value) > 128:
        raise ValueError("密码不能超过 128 个字符")
    if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
        raise ValueError("密码必须同时包含字母和数字")
    return value


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=30)
    email: str = Field(max_length=120)
    password: str
    display_name: str | None = Field(default=None, max_length=30)
    is_student: bool = True
    campus: str = Field(default="主校区", max_length=50)

    @field_validator("username")
    @classmethod
    def username_valid(cls, value: str) -> str:
        if not USERNAME_RE.match(value):
            raise ValueError("用户名需为 3-30 个字符，且不能包含空格")
        return value

    @field_validator("email")
    @classmethod
    def email_valid(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("邮箱格式不正确")
        return value.lower()

    @field_validator("password")
    @classmethod
    def password_valid(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=120, description="用户名或邮箱")
    password: str = Field(min_length=1, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_valid(cls, value: str) -> str:
        return validate_password_strength(value)


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1, max_length=30)
    campus: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=300)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_student: bool | None = None

    @field_validator("avatar_url")
    @classmethod
    def avatar_url_valid(cls, value: str | None) -> str | None:
        return _validate_url(value)


def _validate_url(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") and not value.startswith("/"):
        raise ValueError("图片地址必须是 http(s) URL 或站内绝对路径")
    return value


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5, max_length=2000)
    price: Decimal = Field(gt=0, le=Decimal("999999.99"))
    category: str = Field(max_length=30)
    image_url: str = Field(default="", max_length=500)
    campus: str = Field(default="主校区", max_length=50)

    @field_validator("price")
    @classmethod
    def price_valid(cls, value: Decimal) -> Decimal:
        try:
            return as_money(value)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("价格格式不正确") from exc

    @field_validator("category")
    @classmethod
    def category_valid(cls, value: str) -> str:
        if value not in PRODUCT_CATEGORIES:
            raise ValueError("请选择有效分类")
        return value

    @field_validator("image_url")
    @classmethod
    def image_url_valid(cls, value: str) -> str:
        return _validate_url(value) or ""


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, min_length=5, max_length=2000)
    price: Decimal | None = Field(default=None, gt=0, le=Decimal("999999.99"))
    category: str | None = Field(default=None, max_length=30)
    image_url: str | None = Field(default=None, max_length=500)
    campus: str | None = Field(default=None, max_length=50)
    status: str | None = None

    @field_validator("price")
    @classmethod
    def price_valid(cls, value: Decimal | None) -> Decimal | None:
        return as_money(value) if value is not None else None

    @field_validator("category")
    @classmethod
    def category_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in PRODUCT_CATEGORIES:
            raise ValueError("请选择有效分类")
        return value

    @field_validator("image_url")
    @classmethod
    def image_url_valid(cls, value: str | None) -> str | None:
        return _validate_url(value)

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str | None) -> str | None:
        # 已下架只能由管理员操作。
        if value is not None and value not in ("在售", "已预订", "已售出"):
            raise ValueError("商品状态不合法")
        return value

    @model_validator(mode="after")
    def has_changes(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("至少需要提交一个需要修改的字段")
        return self


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=500)


class OrderCreateRequest(BaseModel):
    product_id: int = Field(gt=0)


class OrderStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str) -> str:
        if value not in ORDER_STATUSES:
            raise ValueError("订单状态不合法")
        return value


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def role_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in ("user", "admin"):
            raise ValueError("用户角色不合法")
        return value

    @model_validator(mode="after")
    def has_changes(self):
        if self.is_active is None and self.role is None:
            raise ValueError("至少需要提交一个需要修改的字段")
        return self


class TakedownRequest(BaseModel):
    reason: str = Field(default="违反平台规范", max_length=200)
