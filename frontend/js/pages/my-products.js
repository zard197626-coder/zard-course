(function () {
  "use strict";

  const list = document.getElementById("my-products-list");
  const count = document.getElementById("my-products-count");
  let status = "";

  function thumb(item) {
    const url = App.safeUrl(item.image_url);
    if (!url) return '<div class="media-placeholder">' + App.categoryEmoji(item.category) + "</div>";
    return '<img src="' + App.escapeHtml(url) + '" alt="' + App.escapeHtml(item.name) + '" onerror="App.imageError(this)">';
  }

  function renderItem(item) {
    const canDelete = ["在售", "已售出"].includes(item.status);
    return (
      '<article class="manage-item">' +
        '<a class="manage-thumb" href="product.html?id=' + item.id + '">' + thumb(item) + "</a>" +
        "<div>" +
          '<h3 class="manage-title"><a href="product.html?id=' + item.id + '">' + App.escapeHtml(item.name) + "</a></h3>" +
          '<div class="row-between" style="justify-content:flex-start;gap:9px">' +
            '<span class="status-badge ' + App.statusClass(item.status) + '">' + App.escapeHtml(item.status) + "</span>" +
            '<span class="price"><span class="currency">¥</span>' + App.money(item.price) + "</span>" +
          "</div>" +
          '<div class="muted tiny" style="margin-top:5px">♡ ' + Number(item.favorite_count || 0) + " 收藏 · 💬 " +
            Number(item.message_count || 0) + " 留言 · " + App.dateTime(item.created_at) + "</div>" +
        "</div>" +
        '<div class="manage-actions">' +
          '<a class="btn btn-ghost btn-sm" href="product.html?id=' + item.id + '">查看</a>' +
          (item.status === "已下架"
            ? '<span class="muted tiny">管理员已下架</span>'
            : '<a class="btn btn-outline btn-sm" href="edit-product.html?id=' + item.id + '">编辑</a>') +
          (canDelete ? '<button class="btn btn-danger btn-sm" type="button" data-delete="' + item.id + '">删除</button>' : "") +
        "</div>" +
      "</article>"
    );
  }

  async function removeItem(id, button) {
    const confirmed = await App.confirmAction("删除后商品将从市场下架，历史订单仍会保留。", "确认删除商品？", "删除");
    if (!confirmed) return;
    App.setButtonLoading(button, true, "删除中");
    try {
      await App.api("/api/products/" + id, { method: "DELETE" });
      App.toast("商品已删除", "success");
      load();
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function load() {
    list.innerHTML = App.loadingState("正在加载我的商品…");
    try {
      const data = await App.api("/api/users/me/products" + App.query({ status: status }));
      count.textContent = "共 " + data.total + " 件商品";
      if (!data.items.length) {
        list.innerHTML = App.emptyState(
          status ? "这个状态下没有商品" : "还没有发布商品",
          status ? "切换其他状态看看，或发布一件新的闲置。" : "整理一下宿舍，把不需要的好物分享给同学吧。",
          '<a class="btn btn-primary" href="publish.html">发布闲置</a>'
        );
        return;
      }
      list.innerHTML = '<div class="manage-list">' + data.items.map(renderItem).join("") + "</div>";
      list.querySelectorAll("[data-delete]").forEach(function (button) {
        button.addEventListener("click", function () { removeItem(Number(button.dataset.delete), button); });
      });
    } catch (error) {
      list.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth("my-products.html")) return;
    document.querySelectorAll("[data-status]").forEach(function (button) {
      button.addEventListener("click", function () {
        status = button.dataset.status;
        document.querySelectorAll("[data-status]").forEach(function (item) {
          item.classList.toggle("active", item === button);
        });
        load();
      });
    });
    load();
  });
})();
