from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

DEFAULT_PASSWORD = "Password123"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(
    client: TestClient,
    username: str,
    *,
    password: str = DEFAULT_PASSWORD,
    is_student: bool = True,
    role: str | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email or f"{username}@example.com",
            "password": password,
            "is_student": is_student,
            "display_name": username,
            "campus": "主校区",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()["data"]
    if role and role != "user":
        client.app.state.db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, payload["user"]["id"]),
        )
        payload["user"]["role"] = role
    return payload


def create_product(
    client: TestClient,
    token: str,
    *,
    name: str = "二手教材",
    description: str = "九成新教材，适合课程复习使用。",
    price: str = "100.00",
    category: str = "教材书籍",
    campus: str = "主校区",
    image_url: str = "",
) -> dict[str, Any]:
    response = client.post(
        "/api/products",
        headers=auth(token),
        json={
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "campus": campus,
            "image_url": image_url,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def login_user(client: TestClient, username: str, password: str = DEFAULT_PASSWORD) -> dict[str, Any]:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"status_code": response.status_code, "body": response.json()}
