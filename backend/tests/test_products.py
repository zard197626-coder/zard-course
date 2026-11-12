from __future__ import annotations

from .helpers import auth, create_product, register_user


def test_create_product_requires_login_and_records_seller(client):
    user = register_user(client, "seller001")
    product = create_product(client, user["token"], name="线性代数教材", price="45.50")
    assert product["name"] == "线性代数教材"
    assert product["price"] == "45.50"
    assert product["status"] == "在售"
    assert product["seller"]["username"] == "seller001"
    assert product["created_at"]


def test_product_search_category_price_and_sort(client):
    user = register_user(client, "seller002")
    token = user["token"]
    create_product(client, token, name="Python 编程教材", price="30.00", category="教材书籍")
    create_product(client, token, name="蓝牙耳机", description="降噪蓝牙耳机，续航良好。", price="120.00", category="电子数码")
    create_product(client, token, name="宿舍台灯", description="护眼台灯，适合宿舍书桌。", price="20.00", category="生活用品")

    search = client.get("/api/products", params={"q": "Python"})
    assert search.status_code == 200
    assert search.json()["data"]["pagination"]["total"] == 1

    category = client.get("/api/products", params={"category": "电子数码"})
    assert [item["name"] for item in category.json()["data"]["items"]] == ["蓝牙耳机"]

    price = client.get("/api/products", params={"min_price": "25", "max_price": "100"})
    assert price.json()["data"]["pagination"]["total"] == 1

    sorted_items = client.get("/api/products", params={"sort": "price_asc"}).json()["data"]["items"]
    assert [item["price"] for item in sorted_items] == ["20.00", "30.00", "120.00"]


def test_product_pagination(client):
    user = register_user(client, "seller003")
    for index in range(5):
        create_product(client, user["token"], name=f"分页商品{index}", price=f"{10 + index}.00")
    first = client.get("/api/products", params={"page": 1, "page_size": 2}).json()["data"]
    second = client.get("/api/products", params={"page": 2, "page_size": 2}).json()["data"]
    assert first["pagination"] == {"page": 1, "page_size": 2, "total": 5, "pages": 3}
    assert len(first["items"]) == 2
    assert len(second["items"]) == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]


def test_product_detail_and_owner_update(client):
    owner = register_user(client, "seller004")
    product = create_product(client, owner["token"])
    detail = client.get(f"/api/products/{product['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["description"].startswith("九成新")

    updated = client.put(
        f"/api/products/{product['id']}",
        headers=auth(owner["token"]),
        json={"price": "88.88", "description": "价格已调整，仍可小刀。"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["price"] == "88.88"


def test_non_owner_cannot_update_or_delete_product(client):
    owner = register_user(client, "seller005")
    other = register_user(client, "seller006")
    product = create_product(client, owner["token"])
    update = client.put(
        f"/api/products/{product['id']}",
        headers=auth(other["token"]),
        json={"price": "1.00"},
    )
    assert update.status_code == 403
    delete = client.delete(f"/api/products/{product['id']}", headers=auth(other["token"]))
    assert delete.status_code == 403


def test_owner_can_delete_product_and_it_disappears(client):
    owner = register_user(client, "seller007")
    product = create_product(client, owner["token"])
    response = client.delete(f"/api/products/{product['id']}", headers=auth(owner["token"]))
    assert response.status_code == 200
    assert client.get(f"/api/products/{product['id']}").status_code == 404
    listing = client.get("/api/products").json()["data"]["items"]
    assert all(item["id"] != product["id"] for item in listing)


def test_product_validation(client):
    user = register_user(client, "seller008")
    response = client.post(
        "/api/products",
        headers=auth(user["token"]),
        json={
            "name": "x",
            "description": "短",
            "price": "-1",
            "category": "不存在的分类",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
