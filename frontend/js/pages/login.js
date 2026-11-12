(function () {
  "use strict";

  function nextTarget() {
    return App.safeNext(new URLSearchParams(location.search).get("next"));
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (Auth.isLoggedIn()) {
      location.replace(nextTarget());
      return;
    }

    const form = document.getElementById("login-form");
    const message = document.getElementById("login-message");
    const registerLink = document.getElementById("register-link");
    const next = new URLSearchParams(location.search).get("next");
    if (next && registerLink) registerLink.href = "register.html?next=" + encodeURIComponent(next);

    document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
      button.addEventListener("click", function () {
        const input = document.getElementById(button.dataset.togglePassword);
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        button.textContent = show ? "隐藏" : "显示";
      });
    });

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const account = document.getElementById("login-account").value.trim();
      const password = document.getElementById("login-password").value;
      if (!account || !password) {
        App.showMessage(message, "请填写用户名/邮箱和密码。", "error");
        return;
      }
      const button = document.getElementById("login-submit");
      App.setButtonLoading(button, true, "登录中");
      try {
        const data = await App.api("/api/auth/login", {
          method: "POST",
          body: { username: account, password: password },
          auth: false,
        });
        Auth.setSession(data);
        App.toast("登录成功，欢迎回来 " + (data.user.display_name || data.user.username), "success");
        setTimeout(function () { location.replace(nextTarget()); }, 250);
      } catch (error) {
        App.showMessage(message, App.errorMessage(error), "error");
        App.setButtonLoading(button, false);
      }
    });
  });
})();
