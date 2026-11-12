from __future__ import annotations

from .helpers import auth, create_product, register_user


def _create_order(client, seller_token, buyer_token, price="100.00", name="订单商品"):
    product = create_product(client, seller_token, name=name, price=price)
    response = client.post("/api/orders", headers=auth(buyer_token), json={"product_id": product["id"]})
    assert response.status_code == 201, response.text
    return product, response.json()["data"]


def test_student_order_gets_ten_percent_discount(client):
    seller = register_user(client, "orderseller1")
    student = register_user(client, "orderstudent1", is_student=True)
    _, order = _create_order(client, seller["token"], student["token"], price="19.99")
    assert order["original_price"] == "19.99"
    assert order["final_price"] == "17.99"
    assert order["discount_amount"] == "2.00"
    assert order["student_discount"] is True
    assert order["status"] == "待确认"


def test_non_student_order_pays_original_price(client):
    seller = register_user(client, "orderseller2")
    teacher = register_user(client, "orderteacher2", is_student=False)
    _, order = _create_order(client, seller["token"], teacher["token"], price="88.80")
    assert order["original_price"] == "88.80"
    assert order["final_price"] == "88.80"
    assert order["discount_amount"] == "0.00"
    assert order["student_discount"] is False


def test_duplicate_purchase_of_reserved_or_sold_product_is_rejected(client):
    seller = register_user(client, "orderseller3")
    buyer = register_user(client, "orderbuyer3")
    other = register_user(client, "orderbuyer4")
    product, _ = _create_order(client, seller["token"], buyer["token"], name="唯一商品")

    second = client.post("/api/orders", headers=auth(other["token"]), json={"product_id": product["id"]})
    assert second.status_code == 409
    detail = client.get(f"/api/products/{product['id']}").json()["data"]
    assert detail["status"] == "已预订"


def test_cannot_buy_own_product(client):
    seller = register_user(client, "orderseller4")
    product = create_product(client, seller["token"])
    response = client.post("/api/orders", headers=auth(seller["token"]), json={"product_id": product["id"]})
    assert response.status_code == 400


def test_seller_confirm_buyer_complete_flow(client):
    seller = register_user(client, "orderseller5")
    buyer = register_user(client, "orderbuyer5")
    product, order = _create_order(client, seller["token"], buyer["token"])
    headers_seller = auth(seller["token"])
    headers_buyer = auth(buyer["token"])

    confirmed = client.put(f"/api/orders/{order['id']}/status", headers=headers_seller, json={"status": "已确认"})
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["status"] == "已确认"

    completed = client.put(f"/api/orders/{order['id']}/status", headers=headers_buyer, json={"status": "已完成"})
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "已完成"
    assert client.get(f"/api/products/{product['id']}").json()["data"]["status"] == "已售出"

    rebuy = client.post("/api/orders", headers=headers_buyer, json={"product_id": product["id"]})
    assert rebuy.status_code == 409


def test_buyer_cancel_returns_product_to_sale(client):
    seller = register_user(client, "orderseller6")
    buyer = register_user(client, "orderbuyer6")
    other = register_user(client, "orderbuyer7")
    product, order = _create_order(client, seller["token"], buyer["token"], name="可取消商品")

    cancelled = client.put(
        f"/api/orders/{order['id']}/status",
        headers=auth(buyer["token"]),
        json={"status": "已取消"},
    )
    assert cancelled.status_code == 200
    assert client.get(f"/api/products/{product['id']}").json()["data"]["status"] == "在售"

    new_order = client.post("/api/orders", headers=auth(other["token"]), json={"product_id": product["id"]})
    assert new_order.status_code == 201


def test_order_permissions_and_invalid_transitions(client):
    seller = register_user(client, "orderseller7")
    buyer = register_user(client, "orderbuyer8")
    outsider = register_user(client, "orderoutsider")
    _, order = _create_order(client, seller["token"], buyer["token"])

    assert client.get(f"/api/orders/{order['id']}", headers=auth(outsider["token"])).status_code == 403
    assert (
        client.put(
            f"/api/orders/{order['id']}/status",
            headers=auth(outsider["token"]),
            json={"status": "已取消"},
        ).status_code
        == 403
    )
    # 买家不能确认订单。
    assert (
        client.put(
            f"/api/orders/{order['id']}/status",
            headers=auth(buyer["token"]),
            json={"status": "已确认"},
        ).status_code
        == 409
    )
    # 待确认不能直接完成。
    assert (
        client.put(
            f"/api/orders/{order['id']}/status",
            headers=auth(seller["token"]),
            json={"status": "已完成"},
        ).status_code
        == 409
    )


def test_order_list_roles_and_unauthorized(client):
    seller = register_user(client, "orderseller8")
    buyer = register_user(client, "orderbuyer9")
    _, order = _create_order(client, seller["token"], buyer["token"])

    buyer_orders = client.get("/api/orders", headers=auth(buyer["token"]), params={"role": "buyer"}).json()["data"]
    assert buyer_orders["pagination"]["total"] == 1
    assert buyer_orders["items"][0]["viewer_role"] == "buyer"
    seller_orders = client.get("/api/orders", headers=auth(seller["token"]), params={"role": "seller"}).json()["data"]
    assert seller_orders["items"][0]["id"] == order["id"]
    assert client.get("/api/orders").status_code == 401


def test_seller_can_cancel_order(client):
    seller = register_user(client, "orderseller9")
    buyer = register_user(client, "orderbuyer10")
    product, order = _create_order(client, seller["token"], buyer["token"])
    response = client.put(
        f"/api/orders/{order['id']}/status",
        headers=auth(seller["token"]),
        json={"status": "已取消"},
    )
    assert response.status_code == 200
    assert client.get(f"/api/products/{product['id']}").json()["data"]["status"] == "在售"
