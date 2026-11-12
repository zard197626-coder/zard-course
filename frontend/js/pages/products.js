(function () {
  "use strict";

  const form = document.getElementById("filter-form");
  const list = document.getElementById("product-list");
  const summary = document.getElementById("result-summary");
  const pagination = document.getElementById("pagination");
  let currentPage = 1;

  function values() {
    const params = new URLSearchParams(location.search);
    return {
      q: params.get("q") || "",
      category: params.get("category") || "",
      campus: params.get("campus") || "",
      min_price: params.get("min_price") || "",
      max_price: params.get("max_price") || "",
      sort: params.get("sort") || "newest",
      page: Math.max(1, Number(params.get("page") || 1)),
      status: params.get("status") || "",
    };
  }

  function fillForm(state) {
    document.getElementById("filter-q").value = state.q;
    document.getElementById("filter-category").value = state.category;
    document.getElementById("filter-campus").value = state.campus;
    document.getElementById("filter-min").value = state.min_price;
    document.getElementById("filter-max").value = state.max_price;
    document.getElementById("filter-sort").value = state.sort;
  }

  function updateUrl(state) {
    const next = App.query(state);
    history.replaceState(null, "", "products.html" + next);
  }

  function updateSummary(data, state) {
    const total = data.pagination ? data.pagination.total : 0;
    const filters = [];
    if (state.q) filters.push("“" + state.q + "”");
    if (state.category) filters.push(state.category);
    if (state.campus) filters.push(state.campus);
    if (state.min_price) filters.push("¥" + state.min_price + " 起");
    summary.textContent = filters.length
      ? "找到 " + total + " 件与 " + filters.join("、") + " 相关的商品"
      : "共找到 " + total + " 件校园好物";
    const count = document.getElementById("active-count");
    if (count) count.textContent = filters.length ? filters.length + " 个筛选条件" : "全部商品";
  }

  async function load(state) {
    currentPage = state.page;
    list.innerHTML = App.productSkeletons(8);
    document.getElementById("product-error").innerHTML = "";
    pagination.innerHTML = "";
    summary.textContent = "正在加载商品…";
    fillForm(state);
    updateUrl(state);

    try {
      const data = await App.api(
        "/api/products" + App.query({
          q: state.q,
          category: state.category,
          campus: state.campus,
          min_price: state.min_price,
          max_price: state.max_price,
          sort: state.sort,
          status: state.status,
          page: state.page,
          page_size: 12,
        }),
        { auth: Auth.isLoggedIn() }
      );
      const items = data.items || [];
      updateSummary(data, state);
      if (!items.length) {
        list.innerHTML = App.emptyState(
          "没有找到匹配的商品",
          "换一个关键词，或者减少筛选条件再试试。也可以发布你的闲置。",
          '<div class="stack-10"><a class="btn btn-primary" href="publish.html">发布闲置</a> <button class="btn btn-ghost" type="button" id="empty-reset">清空筛选</button></div>'
        );
        const emptyReset = document.getElementById("empty-reset");
        if (emptyReset) emptyReset.addEventListener("click", reset);
        return;
      }
      list.innerHTML = items.map(App.productCard).join("");
      App.renderPagination(pagination, data.pagination, function (page) {
        load(Object.assign({}, state, { page: page }));
      });
    } catch (error) {
      list.innerHTML = "";
      document.getElementById("product-error").innerHTML = App.errorState(App.errorMessage(error));
      summary.textContent = "商品加载失败";
    }
  }

  function submitFilters(event) {
    event.preventDefault();
    const state = {
      q: document.getElementById("filter-q").value.trim(),
      category: document.getElementById("filter-category").value,
      campus: document.getElementById("filter-campus").value,
      min_price: document.getElementById("filter-min").value,
      max_price: document.getElementById("filter-max").value,
      sort: document.getElementById("filter-sort").value,
      page: 1,
      status: "",
    };
    if ((state.min_price && Number(state.min_price) < 0) || (state.max_price && Number(state.max_price) < 0)) {
      App.toast("价格不能为负数", "error");
      return;
    }
    if (state.min_price && state.max_price && Number(state.min_price) > Number(state.max_price)) {
      App.toast("最低价格不能高于最高价格", "error");
      return;
    }
    load(state);
  }

  function reset() {
    history.replaceState(null, "", "products.html");
    load(values());
  }

  document.addEventListener("DOMContentLoaded", function () {
    form.addEventListener("submit", submitFilters);
    document.getElementById("reset-filter").addEventListener("click", reset);
    load(values());
  });
})();
