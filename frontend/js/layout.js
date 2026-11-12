/* 全站页头、页脚和移动端导航。 */
(function () {
  "use strict";

  function headerHtml() {
    const user = Auth.getUser();
    const isLoggedIn = Auth.isLoggedIn() && user;
    const adminLink = user && user.role === "admin"
      ? '<a href="admin.html" data-nav="admin">⚙️ 管理后台</a>'
      : "";
    const account = isLoggedIn
      ? '<details class="user-menu">' +
          "<summary>" + App.avatarHtml(user) +
            '<span class="user-name">' + App.escapeHtml(user.display_name || user.username) + "</span>" +
          "</summary>" +
          '<div class="user-dropdown">' +
            '<a href="profile.html">👤 个人中心</a>' +
            '<a href="my-products.html">📦 我的商品</a>' +
            '<a href="orders.html">🧾 我的订单</a>' +
            '<a href="favorites.html">❤️ 我的收藏</a>' +
            adminLink +
            '<div class="divider"></div>' +
            '<button type="button" data-logout>↩️ 退出登录</button>' +
          "</div>" +
        "</details>"
      : '<div class="header-actions"><a class="btn btn-ghost btn-sm" href="login.html">登录</a>' +
        '<a class="btn btn-primary btn-sm" href="register.html">注册</a></div>';

    return (
      '<div class="container header-inner">' +
        '<a class="brand" href="index.html" aria-label="校园集首页">' +
          '<span class="brand-mark">♻</span>' +
          '<span class="brand-text">校园集<small>CAMPUS MARKET</small></span>' +
        "</a>" +
        '<button class="mobile-toggle" type="button" aria-label="打开导航" aria-expanded="false" data-mobile-toggle>☰</button>' +
        '<nav class="site-nav" data-site-nav aria-label="主导航">' +
          '<a href="index.html" data-nav="home">首页</a>' +
          '<a href="products.html" data-nav="products">逛市场</a>' +
          '<a href="publish.html" data-nav="publish">发布闲置</a>' +
          '<a href="orders.html" data-nav="orders">我的订单</a>' +
          account +
        "</nav>" +
      "</div>"
    );
  }

  function footerHtml() {
    return (
      '<div class="container">' +
        '<div class="footer-grid">' +
          '<div class="footer-brand">' +
            '<a class="brand" href="index.html"><span class="brand-mark">♻</span>' +
            '<span class="brand-text">校园集<small>CAMPUS MARKET</small></span></a>' +
            "<p>让闲置在校园里继续流动。面向同学与老师的二手交易练习项目，重视真实、透明与安全。</p>" +
          "</div>" +
          '<div class="footer-col"><h4>逛一逛</h4><a href="products.html">全部商品</a>' +
            '<a href="products.html?sort=newest">最新发布</a><a href="products.html?category=教材书籍">教材书籍</a>' +
            '<a href="products.html?category=电子数码">电子数码</a></div>' +
          '<div class="footer-col"><h4>我的校园集</h4><a href="publish.html">发布闲置</a>' +
            '<a href="orders.html">我的订单</a><a href="favorites.html">我的收藏</a>' +
            '<a href="profile.html">个人资料</a></div>' +
          '<div class="footer-col"><h4>项目说明</h4><span>FastAPI + SQLite</span>' +
            '<span>原生 HTML / CSS / JS</span><span>学生用户享 9 折</span><span>仅用于课程练习</span></div>' +
        "</div>" +
        '<div class="footer-bottom"><span>© 2026 校园集 Campus Market · 校园二手交易练习项目</span>' +
          '<span>交易请优先选择校内公共场所，注意财物安全。</span></div>' +
      "</div>"
    );
  }

  function bindMobileNav() {
    const toggle = document.querySelector("[data-mobile-toggle]");
    const nav = document.querySelector("[data-site-nav]");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", function () {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "✕" : "☰";
    });
  }

  function bindUserMenu() {
    document.addEventListener("click", function (event) {
      document.querySelectorAll("details.user-menu[open]").forEach(function (menu) {
        if (!menu.contains(event.target)) menu.removeAttribute("open");
      });
    });
    const logout = document.querySelector("[data-logout]");
    if (!logout) return;
    logout.addEventListener("click", async function () {
      logout.disabled = true;
      try {
        await App.api("/api/auth/logout", { method: "POST" });
      } catch (_error) {
        // 即使服务端会话已过期，本地也应退出。
      }
      Auth.clear();
      App.toast("已退出登录", "info");
      setTimeout(function () { location.href = "index.html"; }, 250);
    });
  }

  function mount() {
    const header = document.getElementById("site-header");
    const footer = document.getElementById("site-footer");
    if (header) header.className = "site-header", header.innerHTML = headerHtml();
    if (footer) footer.className = "site-footer", footer.innerHTML = footerHtml();
    App.setActiveNav();
    bindMobileNav();
    bindUserMenu();
  }

  document.addEventListener("DOMContentLoaded", mount);
})();
