from __future__ import annotations

import pytest

PAGES = [
    "/",
    "/login.html",
    "/register.html",
    "/products.html",
    "/product.html",
    "/publish.html",
    "/edit-product.html",
    "/favorites.html",
    "/orders.html",
    "/my-products.html",
    "/profile.html",
    "/admin.html",
]


@pytest.mark.parametrize("path", PAGES)
def test_frontend_page_is_served(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()
