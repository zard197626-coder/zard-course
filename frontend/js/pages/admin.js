(function () {
  "use strict";

  const statsBox = document.getElementById("admin-stats");
  const recentBox = document.getElementById("recent-orders");
  const usersBox = document.getElementById("admin-users");
  const productsBox = document.getElementById("admin-products");
  let userQuery = "";
  let productQuery = "";
  let productStatus = "";

  function roleBadge(role) {
    return role === "admin"
      ? '<span class="badge status-info">管理员</span>'
      : '<span class="badge status-neutral">普通用户</span>';
  }

  function renderStats(data) {
    statsBox.innerHTML =
      '<div class="admin-stat-grid">' +
        '<div class="admin-stat"><span class="label">用户数量</span><strong>' + data.users.total + "</strong>" +
          '<span class="sub">活跃 ' + data.users.active + " 人</span></div>" +
        '<div class="admin-stat"><span class="label">商品数量</span><strong>' + data.products.total + "</strong>" +
          '<span class="sub">在售 ' + data.products.on_sale + " 件</span></div>" +
        '<div class="admin-stat"><span class="label">订单数量</span><strong>' + data.orders.total + "</strong>" +
          '<span class="sub">待确认 ' + (data.orders.by_status["待确认"] || 0) + " 笔</span></div>" +
        '<div class="admin-stat"><span class="label">成交金额</span><strong>¥' + App.money(data.sales_amount) + "</strong>" +
          '<span class="sub">已完成 ' + (data.orders.by_status["已完成"] || 0) + " 笔 · 均单 ¥" + App.money(data.average_completed_order) + "</span></div>" +
      "</div>";

    if (!data.recent_orders.length) {
      recentBox.innerHTML = App.emptyState("还没有订单", "平台产生订单后会显示在这里。", "");
      return;
    }
    recentBox.innerHTML =
      '<div class="table-wrap"><table class="data-table"><thead><tr>' +
        "<th>订单号</th><th>商品</th><th>买家</th><th>金额</th><th>状态</th><th>创建时间</th>" +
      "</tr></thead><tbody>" +
        data.recent_orders.map(function (order) {
          return "<tr><td>#" + order.id + "</td><td>" + App.escapeHtml(order.product.name) + "</td><td>" +
            App.escapeHtml(order.buyer.display_name || order.buyer.username) + "</td><td>¥" + App.money(order.final_price) +
            '</td><td><span class="status-badge ' + App.statusClass(order.status) + '">' + order.status + "</span></td><td>" +
            App.dateTime(order.created_at) + "</td></tr>";
        }).join("") +
      "</tbody></table></div>";
  }

  async function loadStats() {
    try {
      const data = await App.api("/api/admin/statistics");
      renderStats(data);
    } catch (error) {
      statsBox.innerHTML = App.errorState(App.errorMessage(error));
      recentBox.innerHTML = "";
    }
  }

  function renderUsers(data) {
    document.getElementById("admin-user-count").textContent = "共 " + data.pagination.total + " 位用户";
    if (!data.items.length) {
      usersBox.innerHTML = App.emptyState("没有匹配用户", "换一个关键词试试。", "");
      return;
    }
    usersBox.innerHTML =
      '<table class="data-table"><thead><tr><th>用户</th><th>角色</th><th>身份</th><th>商品 / 订单</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
      data.items.map(function (item) {
        const self = Auth.getUser() && Auth.getUser().id === item.id;
        return (
          "<tr>" +
            '<td><div class="table-user">' + App.avatarHtml(item) + "<div><strong>" + App.escapeHtml(item.display_name || item.username) +
              '</strong><div class="muted tiny">@' + App.escapeHtml(item.username) + " · " + App.escapeHtml(item.email || "") + "</div></div></div></td>" +
            "<td>" + roleBadge(item.role) + "</td>" +
            "<td>" + (item.is_student ? '<span class="badge status-success">学生</span>' : '<span class="badge status-neutral">非学生</span>') + "</td>" +
            '<td><span class="tiny">' + item.product_count + " 件商品 · " + item.purchase_count + " 笔买入 · " + item.sale_count + " 笔卖出</span></td>" +
            "<td>" + (item.is_active ? '<span class="badge status-success">正常</span>' : '<span class="badge status-cancelled">已停用</span>') + "</td>" +
            '<td><div class="table-actions">' +
              (self
                ? '<span class="muted tiny">当前账号</span>'
                : '<button class="btn btn-ghost btn-sm" data-user-active="' + item.id + '" data-active="' + (item.is_active ? "0" : "1") + '">' +
                    (item.is_active ? "停用" : "启用") + "</button>" +
                  '<button class="btn btn-ghost btn-sm" data-user-role="' + item.id + '" data-role="' + (item.role === "admin" ? "user" : "admin") + '">' +
                    (item.role === "admin" ? "取消管理员" : "设为管理员") + "</button>") +
            "</div></td>" +
          "</tr>"
        );
      }).join("") +
      "</tbody></table>";

    usersBox.querySelectorAll("[data-user-active]").forEach(function (button) {
      button.addEventListener("click", function () {
        updateUser(Number(button.dataset.userActive), { is_active: button.dataset.active === "1" }, button);
      });
    });
    usersBox.querySelectorAll("[data-user-role]").forEach(function (button) {
      button.addEventListener("click", function () {
        updateUser(Number(button.dataset.userRole), { role: button.dataset.role }, button);
      });
    });
  }

  async function loadUsers() {
    usersBox.innerHTML = App.loadingState("加载用户…");
    try {
      const data = await App.api("/api/admin/users" + App.query({ q: userQuery, page_size: 50 }));
      renderUsers(data);
    } catch (error) {
      usersBox.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  async function updateUser(id, body, button) {
    const label = body.role ? (body.role === "admin" ? "设为管理员" : "取消管理员") : (body.is_active ? "启用账号" : "停用账号");
    const confirmed = await App.confirmAction("确认对用户执行“" + label + "”操作吗？", "用户管理", "确认");
    if (!confirmed) return;
    App.setButtonLoading(button, true, "处理中");
    try {
      await App.api("/api/admin/users/" + id, { method: "PUT", body: body });
      App.toast("用户信息已更新", "success");
      await Promise.all([loadUsers(), loadStats()]);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  function renderProducts(data) {
    document.getElementById("admin-product-count").textContent = "共 " + data.pagination.total + " 件商品";
    if (!data.items.length) {
      productsBox.innerHTML = App.emptyState("没有匹配商品", "换一个筛选条件试试。", "");
      return;
    }
    productsBox.innerHTML =
      '<table class="data-table"><thead><tr><th>商品</th><th>卖家</th><th>价格</th><th>状态</th><th>互动</th><th>操作</th></tr></thead><tbody>' +
      data.items.map(function (item) {
        let action = "";
        if (item.is_deleted) {
          action = '<span class="muted tiny">卖家已删除</span>';
        } else if (item.status === "已下架") {
          action = '<button class="btn btn-ghost btn-sm" data-restore="' + item.id + '">恢复上架</button>';
        } else {
          action = '<button class="btn btn-danger btn-sm" data-takedown="' + item.id + '">下架</button>';
        }
        return (
          "<tr>" +
            '<td><div class="table-user"><div class="manage-thumb" style="width:46px;height:38px">' +
              (App.safeUrl(item.image_url)
                ? '<img src="' + App.escapeHtml(App.safeUrl(item.image_url)) + '" alt="" onerror="App.imageError(this)">'
                : '<div class="media-placeholder" style="font-size:1rem">' + App.categoryEmoji(item.category) + "</div>") +
              "</div><div><strong>" + App.escapeHtml(item.name) + '</strong><div class="muted tiny">#' + item.id + " · " +
              App.escapeHtml(item.category) + "</div></div></div></td>" +
            "<td>" + App.escapeHtml(item.seller.display_name || item.seller.username) + "</td>" +
            "<td>¥" + App.money(item.price) + "</td>" +
            '<td><span class="status-badge ' + App.statusClass(item.status) + '">' + item.status + "</span></td>" +
            '<td><span class="tiny">♡ ' + item.favorite_count + " · 💬 " + item.message_count + "</span></td>" +
            '<td><div class="table-actions">' + action +
              '<a class="btn btn-ghost btn-sm" href="product.html?id=' + item.id + '">查看</a></div></td>' +
          "</tr>"
        );
      }).join("") +
      "</tbody></table>";

    productsBox.querySelectorAll("[data-takedown]").forEach(function (button) {
      button.addEventListener("click", function () { takedown(Number(button.dataset.takedown), button); });
    });
    productsBox.querySelectorAll("[data-restore]").forEach(function (button) {
      button.addEventListener("click", function () { restore(Number(button.dataset.restore), button); });
    });
  }

  async function loadProducts() {
    productsBox.innerHTML = App.loadingState("加载商品…");
    try {
      const data = await App.api(
        "/api/admin/products" + App.query({ q: productQuery, status: productStatus, include_deleted: true, page_size: 50 })
      );
      renderProducts(data);
    } catch (error) {
      productsBox.innerHTML = App.errorState(App.errorMessage(error));
    }
  }

  async function takedown(id, button) {
    const confirmed = await App.confirmAction("下架后商品会从市场隐藏，卖家无法自行恢复。确认下架该商品吗？", "下架违规商品", "确认下架");
    if (!confirmed) return;
    App.setButtonLoading(button, true, "处理中");
    try {
      await App.api("/api/admin/products/" + id + "/takedown", {
        method: "PUT",
        body: { reason: "管理员审核后下架" },
      });
      App.toast("商品已下架", "success");
      await Promise.all([loadProducts(), loadStats()]);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function restore(id, button) {
    const confirmed = await App.confirmAction("确认恢复该商品上架吗？若商品存在进行中的订单，将保持“已预订”。", "恢复商品", "恢复上架");
    if (!confirmed) return;
    App.setButtonLoading(button, true, "处理中");
    try {
      await App.api("/api/admin/products/" + id + "/restore", { method: "PUT" });
      App.toast("商品已恢复上架", "success");
      await Promise.all([loadProducts(), loadStats()]);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth("admin.html")) return;
    if (!Auth.isAdmin()) {
      document.querySelector("main .container").innerHTML = App.emptyState(
        "需要管理员权限",
        "当前账号不是管理员，无法访问后台。请使用管理员账号登录。",
        '<a class="btn btn-primary" href="index.html">返回首页</a>'
      );
      return;
    }

    document.getElementById("admin-refresh").addEventListener("click", function () {
      loadStats();
      loadUsers();
      loadProducts();
      App.toast("正在刷新数据", "info");
    });
    document.getElementById("user-search-form").addEventListener("submit", function (event) {
      event.preventDefault();
      userQuery = document.getElementById("user-search").value.trim();
      loadUsers();
    });
    document.getElementById("user-search-reset").addEventListener("click", function () {
      document.getElementById("user-search").value = "";
      userQuery = "";
      loadUsers();
    });
    document.getElementById("product-search-form").addEventListener("submit", function (event) {
      event.preventDefault();
      productQuery = document.getElementById("product-search").value.trim();
      productStatus = document.getElementById("product-status").value;
      loadProducts();
    });

    loadStats();
    loadUsers();
    loadProducts();
  });
})();
