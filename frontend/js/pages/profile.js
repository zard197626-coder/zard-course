(function () {
  "use strict";

  const profileCard = document.getElementById("profile-card");
  const messageBox = document.getElementById("profile-messages");
  let user = null;
  let messageScope = "authored";
  let stats = { products: 0, favorites: 0, orders: 0, messages: 0 };

  function renderProfileCard() {
    profileCard.innerHTML =
      App.avatarHtml(user) +
      "<h2>" + App.escapeHtml(user.display_name || user.username) + "</h2>" +
      '<p class="muted small" style="margin:5px 0 0">@' + App.escapeHtml(user.username) + "</p>" +
      '<div style="margin-top:9px"><span class="badge badge-soft">' + (user.role === "admin" ? "管理员" : "校园用户") + "</span> " +
        '<span class="badge ' + (user.is_student ? "status-success" : "status-neutral") + '">' +
        (user.is_student ? "学生 9 折" : "非学生") + "</span></div>" +
      '<p class="muted small" style="margin-top:13px;white-space:pre-wrap">' + App.escapeHtml(user.bio || "还没有填写个人简介。") + "</p>" +
      '<div class="profile-stats">' +
        '<div class="profile-stat"><strong>' + stats.products + "</strong><span>我的商品</span></div>" +
        '<div class="profile-stat"><strong>' + stats.favorites + "</strong><span>我的收藏</span></div>" +
        '<div class="profile-stat"><strong>' + stats.orders + "</strong><span>我的订单</span></div>" +
      "</div>" +
      '<div class="form-actions" style="justify-content:center"><a class="btn btn-ghost btn-sm" href="orders.html">查看订单</a>' +
        '<a class="btn btn-ghost btn-sm" href="favorites.html">查看收藏</a></div>';
  }

  function fillForm() {
    document.getElementById("profile-name").value = user.display_name || user.username;
    document.getElementById("profile-campus").value = user.campus || "主校区";
    document.getElementById("profile-avatar").value = user.avatar_url || "";
    document.getElementById("profile-bio").value = user.bio || "";
    document.getElementById("profile-student").checked = Boolean(user.is_student);
  }

  async function loadStats() {
    const results = await Promise.allSettled([
      App.api("/api/users/me/products"),
      App.api("/api/users/me/favorites?page_size=1"),
      App.api("/api/orders?role=all&page_size=1"),
      App.api("/api/users/me/messages?scope=authored"),
    ]);
    stats.products = results[0].status === "fulfilled" ? results[0].value.total : 0;
    stats.favorites = results[1].status === "fulfilled" ? results[1].value.pagination.total : 0;
    stats.orders = results[2].status === "fulfilled" ? results[2].value.pagination.total : 0;
    stats.messages = results[3].status === "fulfilled" ? results[3].value.total : 0;
    renderProfileCard();
  }

  function renderMessages(data) {
    if (!data.items.length) {
      messageBox.innerHTML = App.emptyState(
        messageScope === "authored" ? "还没有发出留言" : "还没有收到留言",
        messageScope === "authored" ? "在商品详情页可以向卖家询问成色和交易方式。" : "买家在你商品下的留言会出现在这里。",
        '<a class="btn btn-ghost btn-sm" href="' + (messageScope === "authored" ? "products.html" : "my-products.html") + '">去看看</a>'
      );
      return;
    }
    messageBox.innerHTML =
      '<div class="message-list">' +
        data.items.map(function (message) {
          return (
            '<div class="message-item">' + App.avatarHtml(message.author) + "<div>" +
              '<div class="message-head"><span class="message-author">' +
                App.escapeHtml(message.author.display_name || message.author.username) +
                '</span><span class="message-time">' + App.timeAgo(message.created_at) + "</span>" +
                (message.can_delete ? '<button class="message-delete" type="button" data-delete-message="' + message.id + '">删除</button>' : "") +
              "</div>" +
              '<p class="message-content">' + App.escapeHtml(message.content) + "</p>" +
              '<div class="tiny" style="margin-top:5px">来自商品 <a href="product.html?id=' + message.product.id + '">' +
                App.escapeHtml(message.product.name) + "</a></div>" +
            "</div></div>"
          );
        }).join("") +
      "</div>";
    messageBox.querySelectorAll("[data-delete-message]").forEach(function (button) {
      button.addEventListener("click", function () { deleteMessage(Number(button.dataset.deleteMessage)); });
    });
  }

  async function loadMessages() {
    messageBox.innerHTML = App.loadingState("正在加载留言…");
    try {
      const data = await App.api("/api/users/me/messages?scope=" + messageScope);
      renderMessages(data);
    } catch (error) {
      messageBox.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  async function deleteMessage(id) {
    const confirmed = await App.confirmAction("确定删除这条留言吗？删除后无法恢复。", "删除留言", "删除");
    if (!confirmed) return;
    try {
      await App.api("/api/messages/" + id, { method: "DELETE" });
      App.toast("留言已删除", "success");
      loadMessages();
      stats.messages = Math.max(0, stats.messages - 1);
      renderProfileCard();
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    }
  }

  async function submitProfile(event) {
    event.preventDefault();
    const message = document.getElementById("profile-message");
    const displayName = document.getElementById("profile-name").value.trim();
    if (!displayName) {
      App.showMessage(message, "昵称不能为空。", "error");
      return;
    }
    const button = document.getElementById("profile-submit");
    App.setButtonLoading(button, true, "保存中");
    try {
      const updated = await App.api("/api/users/me", {
        method: "PUT",
        body: {
          display_name: displayName,
          campus: document.getElementById("profile-campus").value,
          avatar_url: document.getElementById("profile-avatar").value.trim(),
          bio: document.getElementById("profile-bio").value.trim(),
          is_student: document.getElementById("profile-student").checked,
        },
      });
      user = updated;
      Auth.setUser(updated);
      renderProfileCard();
      App.showMessage(message, "资料已保存，页面即将刷新。", "success");
      App.toast("个人资料已更新", "success");
      setTimeout(function () { location.reload(); }, 700);
    } catch (error) {
      App.showMessage(message, App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function submitPassword(event) {
    event.preventDefault();
    const message = document.getElementById("password-message");
    const current = document.getElementById("current-password").value;
    const next = document.getElementById("new-password").value;
    const confirm = document.getElementById("confirm-password").value;
    if (!current || !next) {
      App.showMessage(message, "请填写当前密码和新密码。", "error");
      return;
    }
    if (next.length < 8 || !/[A-Za-z]/.test(next) || !/\d/.test(next)) {
      App.showMessage(message, "新密码至少 8 位，且需同时包含字母和数字。", "error");
      return;
    }
    if (next !== confirm) {
      App.showMessage(message, "两次输入的新密码不一致。", "error");
      return;
    }
    const button = document.getElementById("password-submit");
    App.setButtonLoading(button, true, "修改中");
    try {
      await App.api("/api/users/me/password", {
        method: "PUT",
        body: { current_password: current, new_password: next },
      });
      App.showMessage(message, "密码已修改，其他设备上的登录已失效。", "success");
      App.toast("密码修改成功", "success");
      document.getElementById("password-form").reset();
    } catch (error) {
      App.showMessage(message, App.errorMessage(error), "error");
    } finally {
      App.setButtonLoading(button, false);
    }
  }

  document.addEventListener("DOMContentLoaded", async function () {
    if (!App.requireAuth("profile.html")) return;
    user = Auth.getUser();
    if (!user) {
      location.href = "login.html";
      return;
    }
    fillForm();
    renderProfileCard();
    loadStats();
    loadMessages();

    document.getElementById("profile-form").addEventListener("submit", submitProfile);
    document.getElementById("password-form").addEventListener("submit", submitPassword);
    document.querySelectorAll("[data-scope]").forEach(function (button) {
      button.addEventListener("click", function () {
        messageScope = button.dataset.scope;
        document.querySelectorAll("[data-scope]").forEach(function (item) {
          item.classList.toggle("active", item === button);
        });
        loadMessages();
      });
    });

    try {
      const fresh = await App.api("/api/auth/me");
      user = fresh;
      Auth.setUser(fresh);
      fillForm();
      renderProfileCard();
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    }
  });
})();
