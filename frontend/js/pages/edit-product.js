(function () {
  "use strict";

  const container = document.getElementById("edit-content");
  let productId = null;
  let product = null;

  function preview() {
    const wrapper = document.getElementById("edit-preview");
    if (!wrapper) return;
    const url = App.safeUrl(document.getElementById("edit-image").value.trim());
    if (url) {
      wrapper.innerHTML = '<img src="' + App.escapeHtml(url) + '" alt="商品封面预览" onerror="App.imageError(this)">';
    } else {
      wrapper.innerHTML = '<div class="media-placeholder">' + App.categoryEmoji(document.getElementById("edit-category").value) + "</div>";
    }
  }

  function renderForm() {
    container.innerHTML =
      '<div class="page-head"><div><h1>编辑商品</h1><p>修改价格、描述或商品状态，保存后立即生效。</p></div>' +
        '<a class="btn btn-ghost" href="product.html?id=' + product.id + '">查看详情</a></div>' +
      '<div class="detail-grid">' +
        '<section class="panel panel-pad">' +
          '<form id="edit-form" novalidate>' +
            '<div class="form-grid">' +
              '<div class="form-field full"><label for="edit-name">商品名称 <span class="required">*</span></label>' +
                '<input class="input" id="edit-name" maxlength="80" required></div>' +
              '<div class="form-field full"><label for="edit-description">商品描述 <span class="required">*</span></label>' +
                '<textarea class="textarea" id="edit-description" maxlength="2000" required></textarea></div>' +
              '<div class="form-field"><label for="edit-price">价格（元） <span class="required">*</span></label>' +
                '<input class="input" id="edit-price" type="number" min="0.01" max="999999.99" step="0.01" required></div>' +
              '<div class="form-field"><label for="edit-status">商品状态</label>' +
                '<select class="select" id="edit-status"><option value="在售">在售</option><option value="已预订">已预订</option><option value="已售出">已售出</option></select>' +
                '<p class="form-hint">有进行中的订单时，价格和状态不能修改。</p></div>' +
              '<div class="form-field"><label for="edit-category">分类</label>' +
                '<select class="select" id="edit-category">' +
                  ["教材书籍", "电子数码", "生活用品", "运动户外", "服饰鞋包", "美妆个护", "票券卡券", "其他"].map(function (name) {
                    return '<option value="' + name + '">' + name + "</option>";
                  }).join("") +
                "</select></div>" +
              '<div class="form-field"><label for="edit-campus">所在校区</label>' +
                '<select class="select" id="edit-campus"><option>主校区</option><option>东校区</option><option>西校区</option><option>南校区</option><option>北校区</option></select></div>' +
              '<div class="form-field full"><label for="edit-image">商品图片 URL</label>' +
                '<input class="input" id="edit-image" type="url" maxlength="500" placeholder="https://example.com/image.jpg"></div>' +
            "</div>" +
            '<div class="form-message" id="edit-message" role="alert"></div>' +
            '<div class="form-actions"><button class="btn btn-primary" type="submit" id="edit-submit">保存修改</button>' +
              '<a class="btn btn-ghost" href="my-products.html">返回列表</a>' +
              '<button class="btn btn-danger" type="button" id="edit-delete" style="margin-left:auto">删除商品</button></div>' +
          "</form>" +
        "</section>" +
        '<aside class="side-stack"><div class="panel panel-pad"><h2 style="margin:0 0 12px;font-size:1rem">封面预览</h2>' +
          '<div class="product-media" id="edit-preview" style="border-radius:12px;overflow:hidden"></div>' +
          '<p class="form-hint" style="margin-top:10px">当前商品状态：<span class="status-badge ' + App.statusClass(product.status) + '">' + App.escapeHtml(product.status) + "</span></p></div>" +
          '<div class="panel safety-card"><strong>修改提示</strong><br>如果买家已经下单，建议先与买家沟通，不要随意取消已确认的交易。</div>' +
        "</aside>" +
      "</div>";

    document.getElementById("edit-name").value = product.name;
    document.getElementById("edit-description").value = product.description;
    document.getElementById("edit-price").value = product.price;
    document.getElementById("edit-status").value = ["在售", "已预订", "已售出"].includes(product.status) ? product.status : "在售";
    document.getElementById("edit-category").value = product.category;
    document.getElementById("edit-campus").value = product.campus || "主校区";
    document.getElementById("edit-image").value = product.image_url || "";
    preview();

    document.getElementById("edit-image").addEventListener("input", preview);
    document.getElementById("edit-category").addEventListener("change", preview);
    document.getElementById("edit-form").addEventListener("submit", save);
    document.getElementById("edit-delete").addEventListener("click", removeProduct);
  }

  async function load() {
    try {
      product = await App.api("/api/products/" + productId, { auth: true });
      const user = Auth.getUser();
      if (!user || user.id !== product.seller.id) {
        container.innerHTML = App.emptyState("无权编辑", "只有商品卖家可以编辑这件商品。", '<a class="btn btn-primary" href="products.html">返回市场</a>');
        return;
      }
      renderForm();
    } catch (error) {
      container.innerHTML = App.errorState(App.errorMessage(error)) +
        '<div style="margin-top:16px"><a class="btn btn-primary" href="my-products.html">返回我的商品</a></div>';
    }
  }

  async function save(event) {
    event.preventDefault();
    const name = document.getElementById("edit-name").value.trim();
    const description = document.getElementById("edit-description").value.trim();
    const price = document.getElementById("edit-price").value;
    const message = document.getElementById("edit-message");
    if (name.length < 2 || description.length < 5 || !(Number(price) > 0)) {
      App.showMessage(message, "请填写有效的名称、描述和价格。", "error");
      return;
    }
    const body = {
      name: name,
      description: description,
      price: price,
      category: document.getElementById("edit-category").value,
      campus: document.getElementById("edit-campus").value,
      image_url: document.getElementById("edit-image").value.trim(),
      status: document.getElementById("edit-status").value,
    };
    const button = document.getElementById("edit-submit");
    App.setButtonLoading(button, true, "保存中");
    try {
      const updated = await App.api("/api/products/" + productId, { method: "PUT", body: body });
      App.toast("商品已更新", "success");
      setTimeout(function () { location.href = "product.html?id=" + updated.id; }, 300);
    } catch (error) {
      App.showMessage(message, App.errorMessage(error), "error");
      App.setButtonLoading(button, false);
    }
  }

  async function removeProduct() {
    const confirmed = await App.confirmAction("删除后商品将从市场下架，历史订单仍会保留。", "确认删除商品？", "删除");
    if (!confirmed) return;
    try {
      await App.api("/api/products/" + productId, { method: "DELETE" });
      App.toast("商品已删除", "success");
      setTimeout(function () { location.href = "my-products.html"; }, 300);
    } catch (error) {
      App.toast(App.errorMessage(error), "error");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!App.requireAuth(location.pathname.split("/").pop() + location.search)) return;
    productId = Number(new URLSearchParams(location.search).get("id"));
    if (!productId) {
      container.innerHTML = App.emptyState("商品不存在", "链接缺少有效的商品编号。", '<a class="btn btn-primary" href="my-products.html">返回我的商品</a>');
      return;
    }
    load();
  });
})();
