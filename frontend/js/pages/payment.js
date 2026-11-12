(function () {
  "use strict";

  const container = document.getElementById("payment-content");
  let order = null;
  let orderId = null;

  function thumb(item) {
    const url = App.safeUrl(item.image_url);
    if (!url) return '<div class="media-placeholder">' + App.categoryEmoji("其他") + "</div>";
    return '<img src="' + App.escapeHtml(url) + '" alt="' + App.escapeHtml(item.name) + '" onerror="App.imageError(this)">';
  }

  function sandboxBanner() {
    return (
      '<div class="sandbox-banner"><span>🧪</span><span><strong>这是模拟支付，不是真实支付。</strong> ' +
      "不会请求支付宝、微信、银行或任何第三方支付平台，也不会扣除真实资金；所有支付流水只写入本地 SQLite。</span></div>"
    );
  }

  function renderBlocked(title, description) {
    container.innerHTML =
      sandboxBanner() +
      App.emptyState(title, description, '<a class="btn btn-primary" href="orders.html">返回我的订单</a>');
  }

  function renderSuccess(alreadyPaid) {
    const payment = order.payment;
    container.innerHTML =
      sandboxBanner() +
      '<section class="panel payment-success">' +
        '<div class="payment-success-icon">✓</div>' +
        "<h2>" + (alreadyPaid ? "订单已支付" : "模拟支付成功") + "</h2>" +
        "<p>" + (alreadyPaid ? "这笔订单已经完成模拟支付，无需重复支付。" : "卖家现在可以确认订单了。请按约定完成校内交易。") + "</p>" +
        '<div class="payment-receipt">' +
          "<div><span>订单号</span><strong>#" + order.id + "</strong></div>" +
          "<div><span>支付金额</span><strong>¥" + App.money(order.final_price) + "</strong></div>" +
          "<div><span>支付方式</span><strong>" + App.escapeHtml(payment.method_label || "模拟支付") + "</strong></div>" +
          "<div><span>支付时间</span><strong>" + App.dateTime(payment.paid_at) + "</strong></div>" +
          "<div style=\"grid-column:1/-1\"><span>模拟交易号</span><strong>" + App.escapeHtml(payment.transaction_no) + "</strong></div>" +
        "</div>" +
        '<p class="muted tiny">此交易号仅为沙盒流水，不具备任何真实支付效力。</p>' +
        '<div class="form-actions" style="justify-content:center">' +
          '<a class="btn btn-primary" href="orders.html">查看我的订单</a>' +
          '<a class="btn btn-ghost" href="product.html?id=' + order.product.id + '">返回商品</a>' +
        "</div>" +
      "</section>";
  }

  function renderForm() {
    container.innerHTML =
      sandboxBanner() +
      '<div class="payment-layout">' +
        '<section class="panel mock-gateway">' +
          '<div class="mock-gateway-head">' +
            "<h2>校园集模拟收银台</h2>" +
            "<p>订单 #" + order.id + " · " + App.escapeHtml(order.product.name) + "</p>" +
            '<div class="mock-amount">¥' + App.money(order.final_price) + "<small>待支付</small></div>" +
          "</div>" +
          '<div class="panel-body">' +
            '<div class="mock-card-preview">' +
              '<div class="mock-chip"></div>' +
              '<div class="mock-card-number">0000 0000 0000 0000</div>' +
              '<div class="mock-card-meta"><span>TEST CARD · CAMPUS MARKET</span><span>NO REAL CHARGE</span></div>' +
            "</div>" +
            '<form id="payment-form">' +
              '<p style="margin:0 0 10px;font-weight:700;font-size:.9rem">选择模拟支付方式</p>' +
              '<div class="payment-methods">' +
                '<label class="payment-method"><input type="radio" name="method" value="mock_campus" checked>' +
                  '<span class="payment-method-icon">🎓</span><span><strong>校园卡（模拟）</strong><small>模拟校园卡余额扣款，无真实交易</small></span></label>' +
                '<label class="payment-method"><input type="radio" name="method" value="mock_card">' +
                  '<span class="payment-method-icon">💳</span><span><strong>银行卡（模拟）</strong><small>不要输入任何真实银行卡信息</small></span></label>' +
                '<label class="payment-method"><input type="radio" name="method" value="mock_wallet">' +
                  '<span class="payment-method-icon">📱</span><span><strong>校园钱包（模拟）</strong><small>模拟余额支付，立即生成沙盒流水</small></span></label>' +
              "</div>" +
              '<div class="form-message" id="payment-message" role="alert"></div>' +
              '<button class="btn btn-accent btn-block" type="submit" id="pay-submit" style="margin-top:14px">确认模拟支付 ¥' + App.money(order.final_price) + "</button>" +
              '<button class="btn btn-ghost btn-block" type="button" id="pay-fail" style="margin-top:9px">模拟支付失败（测试）</button>' +
            "</form>" +
            '<p class="form-hint" style="margin-top:12px">测试模式：正常支付会生成成功流水；失败按钮用于演示重试和失败记录，不会扣款。</p>' +
          "</div>" +
        "</section>" +
        '<aside class="side-stack">' +
          '<section class="panel panel-pad">' +
            '<h2 style="margin:0 0 10px;font-size:1rem">订单摘要</h2>' +
            '<div class="payment-summary-item">' +
              '<div class="payment-summary-thumb">' + thumb(order.product) + "</div>" +
              "<div><strong>" + App.escapeHtml(order.product.name) + "</strong>" +
                "<span>订单 #" + order.id + " · " + App.escapeHtml(order.product.campus || "校区待沟通") + "</span>" +
                "<span>卖家：" + App.escapeHtml(order.seller.display_name || order.seller.username) + "</span>" +
              "</div>" +
            "</div>" +
            '<div class="payment-summary-item"><div><strong>商品原价</strong><span>卖家标价</span></div>' +
              '<div style="margin-left:auto;font-weight:700">¥' + App.money(order.original_price) + "</div></div>" +
            (Number(order.discount_amount) > 0
              ? '<div class="payment-summary-item"><div><strong>学生优惠</strong><span>已应用 9 折</span></div>' +
                '<div style="margin-left:auto;font-weight:700;color:var(--success)">-¥' + App.money(order.discount_amount) + "</div></div>"
              : '<div class="payment-summary-item"><div><strong>学生优惠</strong><span>非学生原价</span></div>' +
                '<div style="margin-left:auto;font-weight:700">¥0.00</div></div>') +
            '<div class="payment-total"><span class="muted small">应付金额</span>' +
              '<span class="price">¥' + App.money(order.final_price) + "</span></div>" +
          "</section>" +
          '<div class="panel safety-card"><strong>安全说明</strong><br>模拟网关不会收集姓名、卡号、密码、验证码或任何真实支付凭证。页面上的卡号是固定测试占位符。</div>' +
        "</aside>" +
      "</div>";

    document.getElementById("payment-form").addEventListener("submit", function (event) {
      event.preventDefault();
      pay("success");
    });
    document.getElementById("pay-fail").addEventListener("click", function () {
      pay("failure");
    });
  }

  async function pay(outcome) {
    const selected = document.querySelector('input[name="method"]:checked');
    const method = selected ? selected.value : "mock_campus";
    const button = outcome === "failure" ? document.getElementById("pay-fail") : document.getElementById("pay-submit");
    const message = document.getElementById("payment-message");
    App.setButtonLoading(button, true, outcome === "failure" ? "模拟失败中" : "支付处理中");
    try {
      const data = await App.api("/api/orders/" + orderId + "/pay", {
        method: "POST",
        body: { method: method, outcome: outcome },
      });
      order = data.order;
      App.toast("模拟支付成功", "success");
      renderSuccess(false);
    } catch (error) {
      if (error.code === "PAYMENT_FAILED") {
        App.showMessage(message, "模拟支付失败：这是测试分支，订单仍可重试支付。", "error");
        App.toast("模拟支付失败，可重试", "error");
      } else {
        App.showMessage(message, App.errorMessage(error), "error");
        App.toast(App.errorMessage(error), "error");
      }
      App.setButtonLoading(button, false);
    }
  }

  async function load() {
    try {
      order = await App.api("/api/orders/" + orderId);
      const user = Auth.getUser();
      if (!user || user.id !== order.buyer.id) {
        renderBlocked("只有买家可以支付", "当前账号不是该订单的买家，无法发起模拟支付。");
        return;
      }
      if (order.payment.status === "已退款") {
        renderBlocked("订单已退款", "该订单已经模拟退款，不能再次支付。");
        return;
      }
      if (order.payment.status === "已支付") {
        renderSuccess(true);
        return;
      }
      if (order.status === "已取消") {
        renderBlocked("订单已取消", "取消的订单不能再支付，请重新选择其他商品。");
        return;
      }
      if (order.status === "已完成") {
        renderBlocked("订单已完成", "该订单没有待支付金额。");
        return;
      }
      renderForm();
    } catch (error) {
      container.innerHTML = App.errorState(App.errorMessage(error)) +
        '<div style="margin-top:16px"><a class="btn btn-primary" href="orders.html">返回我的订单</a></div>';
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    orderId = Number(new URLSearchParams(location.search).get("order_id"));
    if (!orderId) {
      container.innerHTML = App.emptyState("缺少订单号", "支付链接不完整，请从我的订单进入支付页面。", '<a class="btn btn-primary" href="orders.html">返回我的订单</a>');
      return;
    }
    if (!App.requireAuth("payment.html?order_id=" + orderId)) return;
    load();
  });
})();
