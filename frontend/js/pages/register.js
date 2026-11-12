(function () {
  "use strict";

  function validate(values) {
    if (!/^\S{3,30}$/.test(values.username)) return "用户名需为 3-30 个字符，且不能包含空格。";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(values.email)) return "请输入有效的邮箱地址。";
    if (values.password.length < 8) return "密码至少需要 8 个字符。";
    if (!/[A-Za-z]/.test(values.password) || !/\d/.test(values.password)) return "密码必须同时包含字母和数字。";
    if (values.password !== values.confirm) return "两次输入的密码不一致。";
    return "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (Auth.isLoggedIn()) {
      location.replace(App.safeNext(new URLSearchParams(location.search).get("next")));
      return;
    }

    const form = document.getElementById("register-form");
    const message = document.getElementById("register-message");
    const next = new URLSearchParams(location.search).get("next");
    const loginLink = document.getElementById("login-link");
    if (next && loginLink) loginLink.href = "login.html?next=" + encodeURIComponent(next);

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
      const values = {
        username: document.getElementById("reg-username").value.trim(),
        email: document.getElementById("reg-email").value.trim(),
        password: document.getElementById("reg-password").value,
        confirm: document.getElementById("reg-confirm").value,
        campus: document.getElementById("reg-campus").value,
        is_student: document.getElementById("reg-student").checked,
      };
      const error = validate(values);
      if (error) {
        App.showMessage(message, error, "error");
        return;
      }
      const button = document.getElementById("register-submit");
      App.setButtonLoading(button, true, "正在注册");
      try {
        const data = await App.api("/api/auth/register", {
          method: "POST",
          auth: false,
          body: {
            username: values.username,
            email: values.email,
            password: values.password,
            display_name: values.username,
            campus: values.campus,
            is_student: values.is_student,
          },
        });
        Auth.setSession(data);
        App.toast("注册成功，欢迎加入校园集", "success");
        setTimeout(function () { location.replace(App.safeNext(next)); }, 350);
      } catch (apiError) {
        App.showMessage(message, App.errorMessage(apiError), "error");
        App.setButtonLoading(button, false);
      }
    });
  });
})();
