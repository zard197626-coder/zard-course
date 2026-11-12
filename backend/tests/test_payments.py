from __future__ import annotations

from .helpers import auth, create_product, register_user


def _unpaid_order(client, prefix, price="66.60"):
    seller = register_user(client, f"{prefix}seller")
    buyer = register_user(client, f"{prefix}buyer", is_student=True)
    product = create_product(client, seller["token"], name=f"{prefix}商品", price=price)
    created = client.post(
        "/api/orders",
        headers=auth(buyer["token"]),
        json={"product_id": product["id"]},
    )
    assert created.status_code == 201, created.text
    return seller, buyer, product, created.json()["data"]


def test_mock_payment_success_and_history(client):
    seller, buyer, _, order = _unpaid_order(client, "paysuccess")
    assert order["payment"]["status"] == "未支付"

    response = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_campus", "outcome": "success"},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["payment"]["status"] == "成功"
    assert data["payment"]["method_label"] == "校园卡（模拟）"
    assert data["payment"]["transaction_no"].startswith("MOCK-")
    assert data["order"]["payment"]["status"] == "已支付"
    assert data["order"]["payment"]["paid_at"]

    detail = client.get(f"/api/orders/{order['id']}", headers=auth(buyer["token"])).json()["data"]
    assert detail["payment"]["status"] == "已支付"
    assert detail["payment"]["transaction_no"] == data["payment"]["transaction_no"]

    history = client.get(
        f"/api/orders/{order['id']}/payments",
        headers=auth(buyer["token"]),
    ).json()["data"]
    assert history["total"] == 1
    assert history["items"][0]["status"] == "成功"


def test_seller_cannot_confirm_unpaid_order(client):
    seller, buyer, _, order = _unpaid_order(client, "payrequired")
    denied = client.put(
        f"/api/orders/{order['id']}/status",
        headers=auth(seller["token"]),
        json={"status": "已确认"},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "PAYMENT_REQUIRED"

    paid = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_card", "outcome": "success"},
    )
    assert paid.status_code == 201
    confirmed = client.put(
        f"/api/orders/{order['id']}/status",
        headers=auth(seller["token"]),
        json={"status": "已确认"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["status"] == "已确认"


def test_only_buyer_can_pay_order(client):
    seller, _, _, order = _unpaid_order(client, "payowner")
    outsider = register_user(client, "payoutsider")
    for token in (seller["token"], outsider["token"]):
        response = client.post(
            f"/api/orders/{order['id']}/pay",
            headers=auth(token),
            json={"method": "mock_card", "outcome": "success"},
        )
        assert response.status_code == 403
    assert client.get(f"/api/orders/{order['id']}", headers=auth(seller["token"])).json()["data"]["payment"]["status"] == "未支付"


def test_duplicate_payment_is_rejected(client):
    _, buyer, _, order = _unpaid_order(client, "payduplicate")
    first = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_card", "outcome": "success"},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_card", "outcome": "success"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ALREADY_PAID"
    count = client.app.state.db.fetch_one(
        "SELECT COUNT(*) AS count FROM payments WHERE order_id = ?",
        (order["id"],),
    )
    assert count["count"] == 1


def test_failed_mock_payment_can_retry(client):
    _, buyer, _, order = _unpaid_order(client, "payfailed")
    failed = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_wallet", "outcome": "failure"},
    )
    assert failed.status_code == 402
    assert failed.json()["error"]["code"] == "PAYMENT_FAILED"
    assert failed.json()["error"]["details"]["retryable"] is True

    unpaid = client.get(f"/api/orders/{order['id']}", headers=auth(buyer["token"])).json()["data"]
    assert unpaid["payment"]["status"] == "未支付"
    failed_row = client.app.state.db.fetch_one(
        "SELECT status, failure_reason FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
        (order["id"],),
    )
    assert failed_row["status"] == "失败"
    assert "模拟支付失败" in failed_row["failure_reason"]

    retry = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_wallet", "outcome": "success"},
    )
    assert retry.status_code == 201
    assert retry.json()["data"]["order"]["payment"]["status"] == "已支付"


def test_cancelled_paid_order_is_refunded(client):
    seller, buyer, product, order = _unpaid_order(client, "payrefund", price="100.00")
    paid = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "mock_card", "outcome": "success"},
    )
    assert paid.status_code == 201
    cancelled = client.put(
        f"/api/orders/{order['id']}/status",
        headers=auth(buyer["token"]),
        json={"status": "已取消"},
    )
    assert cancelled.status_code == 200
    payment = cancelled.json()["data"]["payment"]
    assert payment["status"] == "已退款"
    assert payment["refund_amount"] == "90.00"
    assert payment["refunded_at"]
    assert client.get(f"/api/products/{product['id']}").json()["data"]["status"] == "在售"

    record = client.app.state.db.fetch_one(
        "SELECT status, refunded_at FROM payments WHERE order_id = ? AND status = '已退款'",
        (order["id"],),
    )
    assert record is not None
    assert record["refunded_at"]


def test_payment_validation_and_history_permissions(client):
    _, buyer, _, order = _unpaid_order(client, "payvalid")
    invalid = client.post(
        f"/api/orders/{order['id']}/pay",
        headers=auth(buyer["token"]),
        json={"method": "real_bank_card", "outcome": "success"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    outsider = register_user(client, "payvalidoutsider")
    assert client.get(
        f"/api/orders/{order['id']}/payments",
        headers=auth(outsider["token"]),
    ).status_code == 403
    assert client.get(
        f"/api/orders/{order['id']}/payments",
        headers=auth(buyer["token"]),
    ).status_code == 200
