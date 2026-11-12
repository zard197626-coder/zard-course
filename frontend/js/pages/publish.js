(function () {
  "use strict";

  function preview() {
    const wrapper = document.getElementById("publish-preview");
    if (!wrapper) return;
    const url = App.safeUrl(document.getElementById("product-image").value.trim());
    if (url) {
      wrapper.innerHTML = '<img src="' + App.escapeHtml(url) + '" alt="商品封面预览" onerror="App.imageError(this)">';
    } else {
      wrapper.innerHTML = '<div class="media-placeholder">📦</div>';
    }
  }

  function validate(values) {
    if (values.name.length < 2) return "商品名称至少需要 2 个字符。";
    if (values.description.length < 5) return "商品描述至少需要 5 个字符。";
    if (!(Number(values.price) > 0)) return "请输入大于 0 的商品价格。";
    if (!values.category) return "请选择商品分类。";
    return "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth("publish.html")) return;
    const form = document.getElementById("publish-form");
    const message = document.getElementById("publish-message");
    document.getElementById("product-image").addEventListener("input", preview);

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const values = {
        name: document.getElementById("product-name").value.trim(),
        description: document.getElementById("product-description").value.trim(),
        price: document.getElementById("product-price").value,
        category: document.getElementById("product-category").value,
        campus: document.getElementById("product-campus").value,
        image_url: document.getElementById("product-image").value.trim(),
      };
      const error = validate(values);
      if (error) {
        App.showMessage(message, error, "error");
        return;
      }
      const button = document.getElementById("publish-submit");
      App.setButtonLoading(button, true, "发布中");
      try {
        const product = await App.api("/api/products", { method: "POST", body: values });
        App.toast("商品发布成功", "success");
        setTimeout(function () { location.href = "product.html?id=" + product.id; }, 300);
      } catch (apiError) {
        App.showMessage(message, App.errorMessage(apiError), "error");
        App.setButtonLoading(button, false);
      }
    });
  });
})();
