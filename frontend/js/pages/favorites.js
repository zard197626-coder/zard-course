(function () {
  "use strict";

  const list = document.getElementById("favorite-list");
  const pagination = document.getElementById("favorite-pagination");
  let page = 1;

  async function load(targetPage) {
    page = targetPage || 1;
    list.innerHTML = App.productSkeletons(8);
    pagination.innerHTML = "";
    try {
      const data = await App.api("/api/users/me/favorites?page=" + page + "&page_size=12");
      if (!data.items.length) {
        list.innerHTML = App.emptyState(
          "还没有收藏",
          "逛市场时点击商品详情页的“收藏”，喜欢的商品就会出现在这里。",
          '<a class="btn btn-primary" href="products.html">去逛市场</a>'
        );
        return;
      }
      list.innerHTML = data.items
        .map(function (product) {
          return (
            '<div class="favorite-card">' +
              App.productCard(product) +
              '<button class="btn btn-danger btn-sm btn-block" type="button" data-remove="' + product.id + '">取消收藏</button>' +
            "</div>"
          );
        })
        .join("");
      list.querySelectorAll("[data-remove]").forEach(function (button) {
        button.addEventListener("click", function () { removeFavorite(Number(button.dataset.remove), button); });
      });
      App.renderPagination(pagination, data.pagination, load);
    } catch (error) {
      list.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  async function removeFavorite(id, button) {
    App.setButtonLoading(button, true, "处理中");
    try {
      await App.api("/api/products/" + id + "/favorite", { method: "DELETE" });
      App.toast("已取消收藏", "info");
      load(page);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth("favorites.html")) return;
    load(1);
  });
})();
