from __future__ import annotations

from .helpers import DEFAULT_PASSWORD, auth, login_user, register_user


def test_health_returns_unified_json(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_register_hashes_password_and_returns_token(client):
    payload = register_user(client, "student001", is_student=True)
    assert payload["token"]
    assert payload["user"]["username"] == "student001"
    assert payload["user"]["role"] == "user"
    assert payload["user"]["is_student"] is True

    row = client.app.state.db.fetch_one(
        "SELECT password_hash FROM users WHERE username = ?", ("student001",)
    )
    assert row is not None
    assert DEFAULT_PASSWORD not in row["password_hash"]
    assert row["password_hash"].startswith("pbkdf2_sha256$")


def test_duplicate_username_and_email_are_rejected(client):
    register_user(client, "student002", email="student002@example.com")
    duplicate_name = client.post(
        "/api/auth/register",
        json={
            "username": "Student002",
            "email": "another@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["error"]["code"] == "USERNAME_TAKEN"

    duplicate_email = client.post(
        "/api/auth/register",
        json={
            "username": "student003",
            "email": "STUDENT002@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )
    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_validation_rejects_weak_password_and_bad_email(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "ab", "email": "not-an-email", "password": "123"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert len(body["error"]["details"]) >= 2


def test_login_by_username_and_email(client):
    register_user(client, "student004", email="student004@example.com")
    by_username = login_user(client, "student004")
    assert by_username["status_code"] == 200
    assert by_username["body"]["data"]["token"]

    response = client.post(
        "/api/auth/login",
        json={"username": "student004@example.com", "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == "student004"


def test_login_with_wrong_password_is_rejected(client):
    register_user(client, "student005")
    result = login_user(client, "student005", "WrongPassword123")
    assert result["status_code"] == 401
    assert result["body"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_requires_token(client):
    response = client.post(
        "/api/products",
        json={
            "name": "无权限商品",
            "description": "未登录时不能发布商品。",
            "price": "10.00",
            "category": "教材书籍",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_logout_invalidates_token(client):
    user = register_user(client, "student006")
    headers = auth(user["token"])
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_profile_and_password_update(client):
    user = register_user(client, "student007")
    headers = auth(user["token"])
    update = client.put(
        "/api/users/me",
        headers=headers,
        json={"display_name": "新昵称", "campus": "东校区", "bio": "喜欢二手好物"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["display_name"] == "新昵称"
    assert update.json()["data"]["campus"] == "东校区"

    wrong = client.put(
        "/api/users/me/password",
        headers=headers,
        json={"current_password": "NotMyPassword1", "new_password": "NewPassword456"},
    )
    assert wrong.status_code == 400

    changed = client.put(
        "/api/users/me/password",
        headers=headers,
        json={"current_password": DEFAULT_PASSWORD, "new_password": "NewPassword456"},
    )
    assert changed.status_code == 200
    assert login_user(client, "student007", DEFAULT_PASSWORD)["status_code"] == 401
    assert login_user(client, "student007", "NewPassword456")["status_code"] == 200
