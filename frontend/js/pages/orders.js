(function () {
  "use strict";

  const list = document.getElementById("order-list");
  const pagination = document.getElementById("order-pagination");
  const statusSelect = document.getElementById("order-status");
  let role = "buyer";
  let page = 1;

  function thumb(order) {
    const url = App.safeUrl(order.product.image_url);
    if (!url) return '<div class="media-placeholder">' + App.categoryEmoji("其他") + "</div>";
    return '<img src="' + App.escapeHtml(url) + '" alt="' + App.escapeHtml(order.product.name) + '" onerror="App.imageError(this)">';
  }

  function actionButtons(order) {
    const buttons = [];
    if (order.status === "待确认") {
      if (order.viewer_role === "seller") {
        buttons.push('<button class="btn btn-primary btn-sm" data-order="' + order.id + '" data-target="已确认">确认订单</button>');
      }
      buttons.push('<button class="btn btn-danger btn-sm" data-order="' + order.id + '" data-target="已取消">取消订单</button>');
    } else if (order.status === "已确认") {
      buttons.push(
        '<button class="btn btn-primary btn-sm" data-order="' + order.id + '" data-target="已完成">' +
          (order.viewer_role === "seller" ? "标记已完成" : "确认收货") +
        "</button>"
      );
      buttons.push('<button class="btn btn-danger btn-sm" data-order="' + order.id + '" data-target="已取消">取消订单</button>');
    }
    return buttons.length ? '<div class="order-actions">' + buttons.join("") + "</div>" : "";
  }

  function renderOrder(order) {
    const roleText = order.viewer_role === "seller"
      ? "买家：" + (order.buyer.display_name || order.buyer.username)
      : "卖家：" + (order.seller.display_name || order.seller.username);
    return (
      '<article class="order-card">' +
        '<div class="order-top"><span>订单号 <strong>#' + order.id + "</strong> · " + App.dateTime(order.created_at) + "</span>" +
          '<span class="status-badge ' + App.statusClass(order.status) + '">' + App.escapeHtml(order.status) + "</span></div>" +
        '<div class="order-body">' +
          '<a class="order-thumb" href="product.html?id=' + order.product.id + '">' + thumb(order) + "</a>" +
          "<div>" +
            '<h3 class="order-name"><a href="product.html?id=' + order.product.id + '">' + App.escapeHtml(order.product.name) + "</a></h3>" +
            '<div class="order-person">' + App.escapeHtml(roleText) + " · " + App.escapeHtml(order.product.campus || "校区待沟通") + "</div>" +
            (order.student_discount ? '<div class="badge badge-soft" style="margin-top:6px">🎓 已享学生 9 折</div>' : "") +
          "</div>" +
          '<div class="order-money"><span class="price">¥' + App.money(order.final_price) + "</span>" +
            '<span class="order-breakdown">原价 ¥' + App.money(order.original_price) +
              (Number(order.discount_amount) > 0 ? " · 优惠 ¥" + App.money(order.discount_amount) : " · 无优惠") +
            "</span></div>" +
        "</div>" +
        (order.status === "待确认" ? '<div class="order-note">等待卖家确认订单，确认后请按约定完成校内交易。</div>' : "") +
        (order.status === "已确认" ? '<div class="order-note">订单已确认，请当面验货并完成交易；完成后点击“' +
          (order.viewer_role === "seller" ? "标记已完成" : "确认收货") + "”。</div>" : "") +
        actionButtons(order) +
      "</article>"
    );
  }

  async function updateStatus(orderId, target, button) {
    const actionText = target === "已取消" ? "取消订单" : target === "已确认" ? "确认订单" : "完成订单";
    const confirmed = await App.confirmAction(
      target === "已取消" ? "取消后商品会重新回到市场，确定取消这笔订单吗？" : "确认将订单状态更新为“" + target + "”？",
      actionText,
      "确认"
    );
    if (!confirmed) return;
    App.setButtonLoading(button, true, "处理中");
    try {
      await App.api("/api/orders/" + orderId + "/status", { method: "PUT", body: { status: target } });
      App.toast("订单已更新为" + target, "success");
      load(page);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function load(targetPage) {
    page = targetPage || 1;
    list.innerHTML = App.loadingState("正在加载订单…");
    pagination.innerHTML = "";
    try {
      const data = await App.api(
        "/api/orders" + App.query({ role: role, status: statusSelect.value, page: page, page_size: 8 })
      );
      if (!data.items.length) {
        list.innerHTML = App.emptyState(
          role === "buyer" ? "还没有购买记录" : "还没有卖出记录",
          role === "buyer" ? "去市场看看同学们正在出手的好物吧。" : "发布闲置后，买家的订单会出现在这里。",
          '<a class="btn btn-primary" href="' + (role === "buyer" ? "products.html" : "publish.html") + '">' +
            (role === "buyer" ? "去逛市场" : "发布闲置") + "</a>"
        );
        return;
      }
      list.innerHTML = '<div class="order-list">' + data.items.map(renderOrder).join("") + "</div>";
      list.querySelectorAll("[data-order]").forEach(function (button) {
        button.addEventListener("click", function () {
          updateStatus(Number(button.dataset.order), button.dataset.target, button);
        });
      });
      App.renderPagination(pagination, data.pagination, load);
    } catch (error) {
      list.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth("orders.html")) return;
    document.querySelectorAll("[data-role]").forEach(function (button) {
      button.addEventListener("click", function () {
        role = button.dataset.role;
        document.querySelectorAll("[data-role]").forEach(function (item) {
          item.classList.toggle("active", item === button);
        });
        load(1);
      });
    });
    statusSelect.addEventListener("change", function () { load(1); });
    load(1);
  });
})();
