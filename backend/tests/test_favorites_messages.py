from __future__ import annotations

from .helpers import auth, create_product, register_user


def test_favorite_add_list_and_remove(client):
    seller = register_user(client, "favseller")
    buyer = register_user(client, "favbuyer")
    product = create_product(client, seller["token"])
    headers = auth(buyer["token"])

    added = client.post(f"/api/products/{product['id']}/favorite", headers=headers)
    assert added.status_code == 200
    assert added.json()["data"]["is_favorited"] is True

    # 重复收藏保持幂等，不产生重复记录。
    again = client.post(f"/api/products/{product['id']}/favorite", headers=headers)
    assert again.status_code == 200
    favorites = client.get("/api/users/me/favorites", headers=headers).json()["data"]
    assert favorites["pagination"]["total"] == 1
    assert favorites["items"][0]["id"] == product["id"]

    removed = client.delete(f"/api/products/{product['id']}/favorite", headers=headers)
    assert removed.status_code == 200
    assert client.get("/api/users/me/favorites", headers=headers).json()["data"]["items"] == []


def test_favorite_requires_login(client):
    seller = register_user(client, "favseller2")
    product = create_product(client, seller["token"])
    response = client.post(f"/api/products/{product['id']}/favorite")
    assert response.status_code == 401


def test_messages_create_list_and_author_delete(client):
    seller = register_user(client, "msgseller")
    buyer = register_user(client, "msgbuyer")
    product = create_product(client, seller["token"])
    created = client.post(
        f"/api/products/{product['id']}/messages",
        headers=auth(buyer["token"]),
        json={"content": "请问可以周末在主校区交易吗？"},
    )
    assert created.status_code == 201
    message = created.json()["data"]
    assert message["author"]["username"] == "msgbuyer"
    assert message["can_delete"] is True

    listed = client.get(f"/api/products/{product['id']}/messages").json()["data"]
    assert listed["total"] == 1
    assert listed["items"][0]["content"].startswith("请问")

    denied = client.delete(f"/api/messages/{message['id']}", headers=auth(seller["token"]))
    assert denied.status_code == 403
    deleted = client.delete(f"/api/messages/{message['id']}", headers=auth(buyer["token"]))
    assert deleted.status_code == 200
    assert client.get(f"/api/products/{product['id']}/messages").json()["data"]["total"] == 0


def test_seller_can_view_received_messages(client):
    seller = register_user(client, "msgseller2")
    buyer = register_user(client, "msgbuyer2")
    product = create_product(client, seller["token"], name="待留言商品")
    client.post(
        f"/api/products/{product['id']}/messages",
        headers=auth(buyer["token"]),
        json={"content": "想了解一下商品成色。"},
    )
    received = client.get("/api/users/me/messages", headers=auth(seller["token"]), params={"scope": "received"})
    assert received.status_code == 200
    assert received.json()["data"]["total"] == 1
    assert received.json()["data"]["items"][0]["product"]["name"] == "待留言商品"

    authored = client.get("/api/users/me/messages", headers=auth(buyer["token"]), params={"scope": "authored"})
    assert authored.json()["data"]["total"] == 1


def test_message_validation_and_login_required(client):
    seller = register_user(client, "msgseller3")
    product = create_product(client, seller["token"])
    anonymous = client.post(f"/api/products/{product['id']}/messages", json={"content": "你好"})
    assert anonymous.status_code == 401
    empty = client.post(
        f"/api/products/{product['id']}/messages",
        headers=auth(seller["token"]),
        json={"content": ""},
    )
    assert empty.status_code == 422
