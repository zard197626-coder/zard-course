(function () {
  "use strict";

  function renderCategories(categories) {
    const container = document.getElementById("category-grid");
    if (!container) return;
    const items = categories.length
      ? categories
      : ["教材书籍", "电子数码", "生活用品", "运动户外", "服饰鞋包", "美妆个护", "票券卡券", "其他"].map(function (name) {
          return { name: name, count: 0 };
        });
    container.innerHTML = items
      .map(function (item) {
        return (
          '<a class="category-card" href="products.html?category=' + encodeURIComponent(item.name) + '">' +
            '<span class="category-emoji">' + App.categoryEmoji(item.name) + "</span>" +
            "<span><strong>" + App.escapeHtml(item.name) + "</strong><small>" + Number(item.count || 0) + " 件在售</small></span>" +
          "</a>"
        );
      })
      .join("");
  }

  function renderProducts(products) {
    const container = document.getElementById("latest-products");
    if (!container) return;
    if (!products.length) {
      container.outerHTML = App.emptyState(
        "还没有上架商品",
        "成为第一个发布闲置的同学，让好物在校园里流动起来。",
        '<a class="btn btn-primary" href="publish.html">发布第一件闲置</a>'
      );
      return;
    }
    container.innerHTML = products.map(App.productCard).join("");
  }

  async function loadOverview() {
    try {
      const data = await App.api("/api/overview", { auth: false });
      document.getElementById("stat-products").textContent = data.on_sale;
      document.getElementById("stat-users").textContent = data.users;
      document.getElementById("stat-orders").textContent = data.completed_orders;
      const categories = data.categories && data.categories.length
        ? data.categories
        : data.all_categories.map(function (name) { return { name: name, count: 0 }; });
      renderCategories(categories.slice(0, 8));
    } catch (error) {
      renderCategories([]);
      App.toast(App.errorMessage(error), "error");
    }
  }

  async function loadLatest() {
    const container = document.getElementById("latest-products");
    try {
      const data = await App.api("/api/products?page=1&page_size=8&sort=newest", { auth: false });
      renderProducts(data.items || []);
    } catch (error) {
      if (container) container.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("hero-search");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        const keyword = document.getElementById("hero-keyword").value.trim();
        location.href = "products.html" + App.query({ q: keyword });
      });
    }
    loadOverview();
    loadLatest();
  });
})();
