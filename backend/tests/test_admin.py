from __future__ import annotations

from .helpers import auth, create_product, login_user, register_user


def _complete_order(client, admin_token, price="100.00"):
    seller = register_user(client, "adminseller")
    buyer = register_user(client, "adminbuyer", is_student=True)
    product = create_product(client, seller["token"], price=price, name="管理员统计商品")
    created = client.post("/api/orders", headers=auth(buyer["token"]), json={"product_id": product["id"]})
    order = created.json()["data"]
    client.put(f"/api/orders/{order['id']}/status", headers=auth(seller["token"]), json={"status": "已确认"})
    client.put(f"/api/orders/{order['id']}/status", headers=auth(buyer["token"]), json={"status": "已完成"})
    return seller, buyer, order


def test_non_admin_cannot_access_admin_api(client):
    user = register_user(client, "normaluser")
    response = client.get("/api/admin/statistics", headers=auth(user["token"]))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_statistics_counts_and_sales(client):
    admin = register_user(client, "admin001", role="admin")
    _complete_order(client, admin["token"], price="100.00")
    response = client.get("/api/admin/statistics", headers=auth(admin["token"]))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["users"]["total"] == 3
    assert data["products"]["total"] == 1
    assert data["orders"]["total"] == 1
    assert data["orders"]["by_status"]["已完成"] == 1
    assert data["sales_amount"] == "90.00"
    assert data["average_completed_order"] == "90.00"


def test_admin_can_list_and_disable_users(client):
    admin = register_user(client, "admin002", role="admin")
    user = register_user(client, "manageduser")
    listing = client.get("/api/admin/users", headers=auth(admin["token"]))
    assert listing.status_code == 200
    assert any(item["username"] == "manageduser" for item in listing.json()["data"]["items"])

    disabled = client.put(
        f"/api/admin/users/{user['user']['id']}",
        headers=auth(admin["token"]),
        json={"is_active": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["is_active"] is False
    assert client.get("/api/auth/me", headers=auth(user["token"])).status_code == 401
    assert login_user(client, "manageduser")["status_code"] == 403

    enabled = client.put(
        f"/api/admin/users/{user['user']['id']}",
        headers=auth(admin["token"]),
        json={"is_active": True},
    )
    assert enabled.status_code == 200
    assert login_user(client, "manageduser")["status_code"] == 200


def test_admin_cannot_disable_self(client):
    admin = register_user(client, "admin003", role="admin")
    response = client.put(
        f"/api/admin/users/{admin['user']['id']}",
        headers=auth(admin["token"]),
        json={"is_active": False},
    )
    assert response.status_code == 400


def test_admin_takedown_and_restore_product(client):
    admin = register_user(client, "admin004", role="admin")
    seller = register_user(client, "takedownseller")
    product = create_product(client, seller["token"], name="违规商品")
    takedown = client.put(
        f"/api/admin/products/{product['id']}/takedown",
        headers=auth(admin["token"]),
        json={"reason": "疑似违规内容"},
    )
    assert takedown.status_code == 200
    assert takedown.json()["data"]["status"] == "已下架"
    assert client.get(f"/api/products/{product['id']}").status_code == 404

    admin_list = client.get("/api/admin/products", headers=auth(admin["token"]))
    assert any(item["id"] == product["id"] for item in admin_list.json()["data"]["items"])

    restore = client.put(
        f"/api/admin/products/{product['id']}/restore",
        headers=auth(admin["token"]),
    )
    assert restore.status_code == 200
    assert restore.json()["data"]["status"] == "在售"
    assert client.get(f"/api/products/{product['id']}").status_code == 200


def test_admin_restore_sold_product_keeps_sold_status(client):
    admin = register_user(client, "admin006", role="admin")
    _, _, order = _complete_order(client, admin["token"], price="50.00")
    product_id = order["product"]["id"]
    client.put(
        f"/api/admin/products/{product_id}/takedown",
        headers=auth(admin["token"]),
        json={"reason": "复核完成订单商品"},
    )
    restore = client.put(
        f"/api/admin/products/{product_id}/restore",
        headers=auth(admin["token"]),
    )
    assert restore.status_code == 200
    assert restore.json()["data"]["status"] == "已售出"


def test_admin_can_delete_message(client):
    admin = register_user(client, "admin005", role="admin")
    seller = register_user(client, "modseller")
    buyer = register_user(client, "modbuyer")
    product = create_product(client, seller["token"])
    message = client.post(
        f"/api/products/{product['id']}/messages",
        headers=auth(buyer["token"]),
        json={"content": "这是一条测试留言。"},
    ).json()["data"]
    response = client.delete(f"/api/messages/{message['id']}", headers=auth(admin["token"]))
    assert response.status_code == 200
