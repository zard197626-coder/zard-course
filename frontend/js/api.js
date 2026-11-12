/* 共享 API 客户端、鉴权状态和 UI 工具。 */
(function (global) {
  "use strict";

  const TOKEN_KEY = "campus_market_token";
  const USER_KEY = "campus_market_user";

  const API_BASE = (function () {
    if (global.API_BASE) return String(global.API_BASE).replace(/\/$/, "");
    if (location.protocol === "file:") return "http://127.0.0.1:8000";
    if (location.port === "5500" || location.port === "5501") return "http://127.0.0.1:8000";
    return "";
  })();

  class ApiClientError extends Error {
    constructor(message, status, code, details) {
      super(message);
      this.name = "ApiClientError";
      this.status = status;
      this.code = code || "API_ERROR";
      this.details = details;
    }
  }

  const Auth = {
    getToken() {
      return localStorage.getItem(TOKEN_KEY) || "";
    },
    getUser() {
      try {
        return JSON.parse(localStorage.getItem(USER_KEY) || "null");
      } catch (_error) {
        return null;
      }
    },
    setSession(data) {
      localStorage.setItem(TOKEN_KEY, data.token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    },
    setUser(user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    },
    clear() {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    },
    isLoggedIn() {
      return Boolean(this.getToken());
    },
    isAdmin() {
      const user = this.getUser();
      return Boolean(user && user.role === "admin");
    },
  };

  async function api(path, options) {
    const opts = Object.assign({ method: "GET", body: undefined, auth: true, quiet: false }, options || {});
    const headers = { Accept: "application/json" };
    const token = Auth.getToken();
    if (opts.auth && token) headers.Authorization = "Bearer " + token;
    let body;
    if (opts.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(opts.body);
    }

    let response;
    try {
      response = await fetch(API_BASE + path, {
        method: opts.method,
        headers,
        body,
      });
    } catch (_error) {
      throw new ApiClientError("无法连接服务器，请确认后端已启动。", 0, "NETWORK_ERROR");
    }

    let payload = null;
    const text = await response.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (_error) {
        payload = null;
      }
    }

    if (!response.ok || (payload && payload.success === false)) {
      const error = (payload && payload.error) || {};
      const message = (payload && payload.message) || "请求失败（HTTP " + response.status + "）";
      if (response.status === 401 && opts.auth) Auth.clear();
      throw new ApiClientError(message, response.status, error.code, error.details);
    }
    return payload ? payload.data : null;
  }

  function query(params) {
    const search = new URLSearchParams();
    Object.keys(params || {}).forEach(function (key) {
      const value = params[key];
      if (value !== undefined && value !== null && value !== "") search.set(key, value);
    });
    const text = search.toString();
    return text ? "?" + text : "";
  }

  function escapeHtml(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function safeUrl(value) {
    const url = String(value || "").trim();
    if (!url) return "";
    if (url.startsWith("/") && !url.startsWith("//")) return url;
    try {
      const parsed = new URL(url, location.href);
      if (parsed.protocol === "http:" || parsed.protocol === "https:") return parsed.href;
    } catch (_error) {
      return "";
    }
    return "";
  }

  function money(value) {
    const number = Number(value || 0);
    return number.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function dateTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function shortDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
  }

  function timeAgo(value) {
    if (!value) return "";
    const timestamp = new Date(value).getTime();
    if (Number.isNaN(timestamp)) return "";
    const diff = Date.now() - timestamp;
    const minute = 60000;
    const hour = 3600000;
    const day = 86400000;
    if (diff < minute) return "刚刚";
    if (diff < hour) return Math.floor(diff / minute) + " 分钟前";
    if (diff < day) return Math.floor(diff / hour) + " 小时前";
    if (diff < day * 7) return Math.floor(diff / day) + " 天前";
    return shortDate(value);
  }

  const CATEGORY_EMOJI = {
    教材书籍: "📚",
    电子数码: "💻",
    生活用品: "🪴",
    运动户外: "🏸",
    服饰鞋包: "🎒",
    美妆个护: "🧴",
    票券卡券: "🎟️",
    其他: "📦",
  };

  function categoryEmoji(category) {
    return CATEGORY_EMOJI[category] || "📦";
  }

  function statusClass(status) {
    return (
      {
        在售: "status-onsale",
        已预订: "status-reserved",
        已售出: "status-sold",
        已下架: "status-off",
        待确认: "status-pending",
        已确认: "status-confirmed",
        已完成: "status-success",
        已取消: "status-cancelled",
      }[status] || "status-neutral"
    );
  }

  function initials(name) {
    const text = String(name || "同学").trim();
    if (!text) return "同";
    return text.slice(0, 1).toUpperCase();
  }

  function avatarHtml(user, extraClass) {
    const name = (user && (user.display_name || user.username)) || "同学";
    const url = safeUrl(user && user.avatar_url);
    const cls = "avatar" + (extraClass ? " " + extraClass : "");
    if (url) {
      return (
        '<span class="' + cls + '"><img src="' + escapeHtml(url) + '" alt="' + escapeHtml(name) +
        '" onerror="this.remove()"></span>'
      );
    }
    return '<span class="' + cls + '">' + escapeHtml(initials(name)) + "</span>";
  }

  function imageBlock(url, alt, extraClass) {
    const src = safeUrl(url);
    if (src) {
      return (
        '<img src="' + escapeHtml(src) + '" alt="' + escapeHtml(alt || "商品图片") +
        '" loading="lazy" onerror="App.imageError(this)">'
      );
    }
    return '<div class="media-placeholder">' + escapeHtml(categoryEmoji("其他")) + "</div>";
  }

  function productCard(product) {
    const image = safeUrl(product.image_url)
      ? '<img src="' + escapeHtml(safeUrl(product.image_url)) + '" alt="' + escapeHtml(product.name) +
        '" loading="lazy" onerror="App.imageError(this)">'
      : '<div class="media-placeholder">' + categoryEmoji(product.category) + "</div>";
    const seller = product.seller || {};
    return (
      '<article class="product-card">' +
        '<div class="product-media">' +
          '<a href="product.html?id=' + product.id + '" aria-label="查看 ' + escapeHtml(product.name) + '">' + image + "</a>" +
          '<span class="status-badge ' + statusClass(product.status) + '">' + escapeHtml(product.status) + "</span>" +
        "</div>" +
        '<div class="product-body">' +
          '<div class="product-category">' + escapeHtml(product.category || "其他") + "</div>" +
          '<h3 class="product-name"><a href="product.html?id=' + product.id + '">' + escapeHtml(product.name) + "</a></h3>" +
          '<div class="product-meta">' +
            '<span>' + escapeHtml(seller.display_name || seller.username || "校园卖家") + "</span>" +
            '<span class="dot"></span><span>' + escapeHtml(product.campus || "校内") + "</span>" +
          "</div>" +
          '<div class="product-price-row">' +
            '<span class="price"><span class="currency">¥</span><span class="amount">' + money(product.price) + "</span></span>" +
            '<span class="favorite-count">♡ ' + Number(product.favorite_count || 0) + "</span>" +
          "</div>" +
        "</div>" +
      "</article>"
    );
  }

  function productSkeletons(count) {
    let html = "";
    for (let i = 0; i < (count || 8); i += 1) {
      html += '<div class="skeleton skeleton-card" aria-hidden="true"></div>';
    }
    return html;
  }

  function toast(message, type) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    const icon = type === "error" ? "!" : type === "info" ? "i" : "✓";
    const item = document.createElement("div");
    item.className = "toast " + (type || "success");
    item.innerHTML =
      '<span class="toast-icon">' + escapeHtml(icon) + '</span><span>' + escapeHtml(message) + "</span>";
    container.appendChild(item);
    setTimeout(function () {
      item.style.opacity = "0";
      item.style.transform = "translateY(6px)";
      item.style.transition = "opacity .2s ease, transform .2s ease";
      setTimeout(function () { item.remove(); }, 220);
    }, 3200);
  }

  function errorMessage(error) {
    if (!error) return "操作失败，请稍后重试。";
    if (error.details && Array.isArray(error.details) && error.details.length) {
      return error.details[0].message || error.message;
    }
    return error.message || "操作失败，请稍后重试。";
  }

  function showMessage(element, message, type) {
    if (!element) return;
    element.textContent = message;
    element.className = "form-message show " + (type || "error");
  }

  function setButtonLoading(button, loading, text) {
    if (!button) return;
    if (loading) {
      button.dataset.originalText = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<span class="btn-spinner"></span><span>' + escapeHtml(text || "处理中…") + "</span>";
    } else {
      button.disabled = false;
      if (button.dataset.originalText) button.innerHTML = button.dataset.originalText;
    }
  }

  function confirmAction(message, title, confirmText) {
    return new Promise(function (resolve) {
      const dialog = document.createElement("dialog");
      dialog.className = "modal";
      dialog.innerHTML =
        '<div class="modal-card">' +
          "<h3>" + escapeHtml(title || "确认操作") + "</h3>" +
          "<p>" + escapeHtml(message) + "</p>" +
          '<div class="modal-actions">' +
            '<button type="button" class="btn btn-ghost" data-cancel>取消</button>' +
            '<button type="button" class="btn btn-primary" data-confirm>' + escapeHtml(confirmText || "确认") + "</button>" +
          "</div>" +
        "</div>";
      document.body.appendChild(dialog);
      dialog.querySelector("[data-cancel]").addEventListener("click", function () {
        dialog.close();
        resolve(false);
      });
      dialog.querySelector("[data-confirm]").addEventListener("click", function () {
        dialog.close();
        resolve(true);
      });
      dialog.addEventListener("close", function () {
        dialog.remove();
        resolve(false);
      });
      dialog.showModal();
    });
  }

  function emptyState(title, description, actionHtml) {
    return (
      '<div class="empty-state">' +
        '<div class="empty-icon">🌱</div>' +
        "<h3>" + escapeHtml(title) + "</h3>" +
        "<p>" + escapeHtml(description) + "</p>" +
        (actionHtml || "") +
      "</div>"
    );
  }

  function loadingState(text) {
    return '<div class="loading-block"><div class="spinner"></div><span>' + escapeHtml(text || "加载中…") + "</span></div>";
  }

  function errorState(message) {
    return '<div class="inline-error">' + escapeHtml(message) + "</div>";
  }

  function pageButtons(pagination) {
    const current = pagination.page;
    const pages = pagination.pages;
    if (pages <= 1) return "";
    const items = [];
    items.push('<button class="page-btn" data-page="' + (current - 1) + '"' + (current <= 1 ? " disabled" : "") + ">上一页</button>");
    const numbers = new Set([1, pages, current - 1, current, current + 1]);
    if (current <= 3) [2, 3, 4].forEach(function (n) { numbers.add(n); });
    if (current >= pages - 2) [pages - 1, pages - 2, pages - 3].forEach(function (n) { numbers.add(n); });
    const sorted = Array.from(numbers).filter(function (n) { return n >= 1 && n <= pages; }).sort(function (a, b) { return a - b; });
    let previous = 0;
    sorted.forEach(function (n) {
      if (previous && n - previous > 1) items.push('<span class="page-btn" aria-hidden="true">…</span>');
      items.push(
        '<button class="page-btn' + (n === current ? " active" : "") + '" data-page="' + n + '"' +
        (n === current ? ' aria-current="page"' : "") + ">" + n + "</button>"
      );
      previous = n;
    });
    items.push('<button class="page-btn" data-page="' + (current + 1) + '"' + (current >= pages ? " disabled" : "") + ">下一页</button>");
    return items.join("");
  }

  function renderPagination(container, pagination, onPage) {
    if (!container) return;
    if (!pagination || pagination.pages <= 1) {
      container.innerHTML = "";
      return;
    }
    container.innerHTML = pageButtons(pagination);
    container.querySelectorAll("[data-page]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (!button.disabled && button.dataset.page) onPage(Number(button.dataset.page));
      });
    });
  }

  function debounce(fn, delay) {
    let timer;
    return function () {
      const args = arguments;
      const context = this;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(context, args); }, delay || 300);
    };
  }

  function loginUrl(next) {
    const target = next || location.pathname.split("/").pop() + location.search;
    return "login.html?next=" + encodeURIComponent(target);
  }

  function requireAuth(next) {
    if (Auth.isLoggedIn()) return true;
    location.href = loginUrl(next);
    return false;
  }

  function safeNext(value) {
    const next = String(value || "").trim();
    if (!next || next.includes("://") || next.startsWith("//") || next.startsWith("javascript:")) return "index.html";
    return next;
  }

  function formDataObject(form) {
    const data = {};
    new FormData(form).forEach(function (value, key) {
      data[key] = value;
    });
    return data;
  }

  function setActiveNav() {
    const page = document.body.dataset.page || "";
    document.querySelectorAll("[data-nav]").forEach(function (link) {
      if (link.dataset.nav === page) link.classList.add("active");
    });
  }

  const App = {
    API_BASE,
    ApiClientError,
    api,
    query,
    escapeHtml,
    safeUrl,
    money,
    dateTime,
    shortDate,
    timeAgo,
    categoryEmoji,
    statusClass,
    initials,
    avatarHtml,
    imageBlock,
    productCard,
    productSkeletons,
    toast,
    errorMessage,
    showMessage,
    setButtonLoading,
    confirmAction,
    emptyState,
    loadingState,
    errorState,
    renderPagination,
    debounce,
    loginUrl,
    requireAuth,
    safeNext,
    formDataObject,
    setActiveNav,
    imageError(img) {
      const wrapper = img.parentElement;
      if (!wrapper) return;
      const placeholder = document.createElement("div");
      placeholder.className = "media-placeholder";
      placeholder.textContent = "📦";
      wrapper.replaceChildren(placeholder);
    },
  };

  global.ApiClientError = ApiClientError;
  global.Auth = Auth;
  global.App = App;
})(window);
