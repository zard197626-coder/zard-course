(function () {
  "use strict";

  const detail = document.getElementById("product-detail");
  const messageSection = document.getElementById("message-section");
  let product = null;
  let productId = null;

  function currentId() {
    const id = Number(new URLSearchParams(location.search).get("id"));
    return Number.isInteger(id) && id > 0 ? id : null;
  }

  function imageHtml(item) {
    const url = App.safeUrl(item.image_url);
    if (!url) return '<div class="media-placeholder" style="font-size:4rem">' + App.categoryEmoji(item.category) + "</div>";
    return '<img src="' + App.escapeHtml(url) + '" alt="' + App.escapeHtml(item.name) + '" onerror="App.imageError(this)">';
  }

  function renderProduct() {
    const user = Auth.getUser();
    const isOwner = Boolean(user && user.id === product.seller.id);
    const studentPrice = (Number(product.price) * 0.9).toFixed(2);
    const canBuy = product.status === "在售" && !isOwner;
    const favoriteText = product.is_favorited ? "♥ 已收藏" : "♡ 收藏";
    const favoriteClass = product.is_favorited ? "btn-danger" : "btn-ghost";

    detail.innerHTML =
      '<div class="detail-grid">' +
        '<article class="panel detail-main">' +
          '<div class="detail-image">' + imageHtml(product) + "</div>" +
          '<div class="detail-content">' +
            '<div class="detail-title-row">' +
              "<div>" +
                '<div class="product-category">' + App.escapeHtml(product.category) + "</div>" +
                '<h1 class="detail-title">' + App.escapeHtml(product.name) + "</h1>" +
                '<span class="status-badge ' + App.statusClass(product.status) + '">' + App.escapeHtml(product.status) + "</span>" +
              "</div>" +
              '<span class="favorite-count">♡ ' + Number(product.favorite_count || 0) + " 人收藏</span>" +
            "</div>" +
            '<div class="detail-price"><span class="price"><span class="currency">¥</span><span class="amount">' + App.money(product.price) + "</span></span>" +
              '<span class="muted small">原价 / 卖家标价</span></div>' +
            '<div class="student-price-note">🎓 学生用户下单自动享 9 折，预计 ¥' + studentPrice + "；最终金额由服务端按 Decimal 计算。" +
              (isOwner ? '<br>这是你发布的商品，不能购买自己的商品。' : "") +
            "</div>" +
            '<div class="detail-facts">' +
              "<span>📍 " + App.escapeHtml(product.campus || "校区待沟通") + "</span>" +
              "<span>🕒 " + App.dateTime(product.created_at) + " 发布</span>" +
              "<span>💬 " + Number(product.message_count || 0) + " 条留言</span>" +
            "</div>" +
            '<div class="detail-desc">' + App.escapeHtml(product.description) + "</div>" +
            (product.moderation_note ? '<p class="form-error" style="margin-top:14px">管理员备注：' + App.escapeHtml(product.moderation_note) + "</p>" : "") +
          "</div>" +
        "</article>" +
        '<aside class="side-stack">' +
          '<div class="panel seller-card">' +
            '<div class="seller-head">' + App.avatarHtml(product.seller) +
              "<div><div class=\"seller-name\">" + App.escapeHtml(product.seller.display_name || product.seller.username) + "</div>" +
              '<div class="muted small">@' + App.escapeHtml(product.seller.username) + " · " + App.escapeHtml(product.seller.campus || "校园卖家") + "</div>" +
              '<div class="' + (product.seller.is_student ? "text-success" : "muted") + ' tiny">' +
                (product.seller.is_student ? "🎓 学生用户" : "👤 非学生用户") + "</div></div>" +
            "</div>" +
            '<div class="buy-actions">' +
              (canBuy
                ? '<button class="btn btn-primary btn-block" type="button" data-buy>立即购买</button>'
                : product.status !== "在售"
                  ? '<button class="btn btn-ghost btn-block" type="button" disabled>商品' + App.escapeHtml(product.status) + "，暂不可购买</button>"
                  : '<button class="btn btn-ghost btn-block" type="button" disabled>不能购买自己的商品</button>') +
              '<div class="action-row">' +
                '<button class="btn ' + favoriteClass + '" type="button" data-favorite>' + favoriteText + "</button>" +
                '<a class="btn btn-ghost" href="#message-section">💬 留言</a>' +
              "</div>" +
              (isOwner
                ? '<div class="action-row"><a class="btn btn-outline" href="edit-product.html?id=' + product.id + '">编辑商品</a>' +
                  '<button class="btn btn-danger" type="button" data-delete>删除</button></div>'
                : "") +
            "</div>" +
          "</div>" +
          '<div class="panel safety-card"><strong>校园交易安全提示</strong><br>优先选择图书馆、教学楼、宿舍楼下等公共场所；当面验货后再付款；不要提前向陌生账户转账。</div>' +
        "</aside>" +
      "</div>";

    const favoriteButton = detail.querySelector("[data-favorite]");
    if (favoriteButton) favoriteButton.addEventListener("click", toggleFavorite);
    const buyButton = detail.querySelector("[data-buy]");
    if (buyButton) buyButton.addEventListener("click", buyProduct);
    const deleteButton = detail.querySelector("[data-delete]");
    if (deleteButton) deleteButton.addEventListener("click", deleteProduct);
  }

  async function loadProduct() {
    detail.innerHTML = '<div class="loading-block"><div class="spinner"></div><span>正在加载商品详情…</span></div>';
    try {
      product = await App.api("/api/products/" + productId, { auth: Auth.isLoggedIn() });
      renderProduct();
      loadMessages();
    } catch (error) {
      detail.innerHTML = App.errorState(App.errorMessage(error)) +
        '<div style="margin-top:16px"><a class="btn btn-primary" href="products.html">返回市场</a></div>';
      messageSection.innerHTML = "";
    }
  }

  async function toggleFavorite() {
    if (!App.requireAuth("product.html?id=" + productId)) return;
    const button = detail.querySelector("[data-favorite]");
    App.setButtonLoading(button, true, "处理中");
    let updated = false;
    try {
      const data = await App.api("/api/products/" + productId + "/favorite", {
        method: product.is_favorited ? "DELETE" : "POST",
      });
      product.is_favorited = data.is_favorited;
      product.favorite_count = data.favorite_count;
      button.disabled = false;
      delete button.dataset.originalText;
      button.className = "btn " + (data.is_favorited ? "btn-danger" : "btn-ghost");
      button.textContent = data.is_favorited ? "♥ 已收藏" : "♡ 收藏";
      const countElement = detail.querySelector(".favorite-count");
      if (countElement) countElement.textContent = "♡ " + data.favorite_count + " 人收藏";
      App.toast(data.is_favorited ? "已加入收藏" : "已取消收藏", "success");
      updated = true;
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    } finally {
      if (!updated) App.setButtonLoading(button, false);
    }
  }

  async function buyProduct() {
    if (!App.requireAuth("product.html?id=" + productId)) return;
    const user = Auth.getUser();
    const expected = user && user.is_student ? (Number(product.price) * 0.9).toFixed(2) : Number(product.price).toFixed(2);
    const confirmed = await App.confirmAction(
      "将以约 ¥" + expected + " 的价格创建订单，最终金额由服务端结算。下单后请等待卖家确认。",
      "确认购买这件商品？",
      "确认下单"
    );
    if (!confirmed) return;
    const button = detail.querySelector("[data-buy]");
    App.setButtonLoading(button, true, "正在下单");
    try {
      const order = await App.api("/api/orders", { method: "POST", body: { product_id: productId } });
      App.toast("订单已创建，请完成模拟支付", "success");
      setTimeout(function () { location.href = "payment.html?order_id=" + order.id; }, 650);
      await loadProduct();
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function deleteProduct() {
    const confirmed = await App.confirmAction("删除后商品将从市场下架，已产生的历史订单仍会保留。", "确认删除商品？", "删除");
    if (!confirmed) return;
    try {
      await App.api("/api/products/" + productId, { method: "DELETE" });
      App.toast("商品已删除", "success");
      setTimeout(function () { location.href = "my-products.html"; }, 400);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    }
  }

  function renderMessageItem(message) {
    return (
      '<div class="message-item">' +
        App.avatarHtml(message.author) +
        "<div>" +
          '<div class="message-head"><span class="message-author">' +
            App.escapeHtml(message.author.display_name || message.author.username) +
            '</span><span class="message-time">' + App.timeAgo(message.created_at) + "</span>" +
            (message.can_delete ? '<button class="message-delete" type="button" data-delete-message="' + message.id + '">删除</button>' : "") +
          "</div>" +
          '<p class="message-content">' + App.escapeHtml(message.content) + "</p>" +
        "</div>" +
      "</div>"
    );
  }

  async function loadMessages() {
    try {
      const data = await App.api("/api/products/" + productId + "/messages", { auth: Auth.isLoggedIn() });
      const form = Auth.isLoggedIn()
        ? '<form class="message-form" id="message-form">' +
            '<input class="input" id="message-content" maxlength="500" placeholder="询问成色、交易地点或时间…" required>' +
            '<button class="btn btn-primary" type="submit">发送留言</button>' +
          "</form>"
        : '<div class="inline-error" style="background:var(--surface-soft);border-color:var(--line);color:var(--muted)">' +
            '<a href="' + App.loginUrl("product.html?id=" + productId) + '">登录</a> 后可以留言和购买。' +
          "</div>";
      messageSection.innerHTML =
        '<section class="panel message-section">' +
          '<div class="panel-head"><h2>留言与沟通</h2><span class="muted small">' + data.total + " 条留言</span></div>" +
          '<div class="panel-body">' + form +
            '<div class="message-list" id="message-list">' +
              (data.items.length
                ? data.items.map(renderMessageItem).join("")
                : '<div class="muted small" style="padding:14px 0">还没有留言，来问第一个问题吧。</div>') +
            "</div>" +
          "</div>" +
        "</section>";

      const formElement = document.getElementById("message-form");
      if (formElement) formElement.addEventListener("submit", submitMessage);
      messageSection.querySelectorAll("[data-delete-message]").forEach(function (button) {
        button.addEventListener("click", function () { deleteMessage(Number(button.dataset.deleteMessage)); });
      });
    } catch (error) {
      messageSection.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  async function submitMessage(event) {
    event.preventDefault();
    const input = document.getElementById("message-content");
    const content = input.value.trim();
    if (!content) {
      App.toast("留言内容不能为空", "error");
      return;
    }
    const button = event.currentTarget.querySelector("button[type=submit]");
    App.setButtonLoading(button, true, "发送中");
    try {
      await App.api("/api/products/" + productId + "/messages", { method: "POST", body: { content: content } });
      App.toast("留言已发送", "success");
      await loadMessages();
      product.message_count = Number(product.message_count || 0) + 1;
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function deleteMessage(messageId) {
    const confirmed = await App.confirmAction("删除后无法恢复，确定删除这条留言吗？", "删除留言", "删除");
    if (!confirmed) return;
    try {
      await App.api("/api/messages/" + messageId, { method: "DELETE" });
      App.toast("留言已删除", "success");
      await loadMessages();
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    productId = currentId();
    if (!productId) {
      detail.innerHTML = App.emptyState("商品不存在", "链接缺少有效的商品编号。", '<a class="btn btn-primary" href="products.html">返回市场</a>');
      return;
    }
    loadProduct();
  });
})();
