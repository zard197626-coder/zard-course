# 校园集 · 校园二手交易平台

一个面向校园场景的全栈二手交易练习项目：学生和老师可以发布闲置、搜索商品、收藏、留言、下单、完成**沙盒模拟支付**，并由卖家确认交易。项目保留了最初的 **学生折扣 checkout 逻辑**，下单时由服务端按学生身份自动计算 9 折，金额使用 `Decimal` 计算并保留两位小数。

- 仓库：<https://github.com/zard197626-coder/zard-course>
- 后端：Python FastAPI + SQLite
- 前端：原生 HTML / CSS / JavaScript（无构建步骤）
- API：RESTful JSON
- 测试：pytest + FastAPI TestClient + unittest

> 本项目仅用于课程练习。项目提供**模拟支付网关**，但**没有接入真实支付平台**、实名认证或物流系统，不会产生真实扣款，请勿用于真实资金交易。

---

## 一、功能列表

### 用户系统

- 用户注册、登录、退出登录
- 密码使用 PBKDF2-HMAC-SHA256 加盐哈希保存，不存明文
- 登录返回随机 Session Token，服务端仅保存 Token 的 SHA-256 摘要
- 普通用户 / 管理员两种角色
- 查看和修改个人资料、修改密码
- 停用账号后无法登录，已有会话立即失效

### 商品系统

- 发布、编辑、删除商品
- 商品字段：名称、描述、价格、分类、图片 URL、校区、状态、发布时间、卖家信息
- 状态：`在售`、`已预订`、`已售出`，管理员可下架为 `已下架`
- 分页、关键词搜索、分类筛选、校区筛选、价格区间筛选
- 按发布时间、价格排序
- 商品详情页展示卖家、收藏数、留言数和商品状态

### 收藏与留言

- 收藏 / 取消收藏，重复收藏幂等
- 查看我的收藏
- 登录用户可在商品详情页留言
- 卖家可以在“个人中心 → 我的留言 → 我收到的”中查看商品留言
- 用户只能删除自己的留言；管理员可删除违规留言

### 订单系统

- 登录用户可以购买商品并创建订单
- 一个商品同时只能存在一条有效订单，已售出商品不能再次购买
- 订单状态：`待确认`、`已确认`、`已完成`、`已取消`
- 卖家确认 / 取消订单
- 买家取消未完成订单，卖家取消待确认或已确认订单
- 订单记录**原价**、**折扣金额**、**最终价格**和学生优惠快照
- 学生用户 9 折，非学生用户原价
- 取消订单后商品自动回到在售；完成订单后商品变为已售出
- 不能购买自己发布的商品

### 模拟支付网关

- 独立的模拟收银台页面 `payment.html`，明确标注“不会产生真实扣款”
- 支付方式：校园卡（模拟）、银行卡（模拟）、校园钱包（模拟）
- 支付状态：`未支付`、`已支付`、`已退款`
- 买家支付成功后，卖家才能确认订单
- 支持生成成功支付流水；提供“模拟支付失败”按钮，用于演示失败与重试
- 支付失败会保留失败流水，订单仍为未支付，可重新支付
- 重复支付会被拒绝
- 取消已支付订单时自动模拟退款，恢复商品在售，并记录退款金额和时间
- 支付流水保存在本地 SQLite 的 `payments` 表，不请求任何第三方支付服务
- 旧数据库会自动迁移支付字段，并将历史已确认/已完成订单回填为“已支付”

### 用户中心

- 我的商品
- 我买到的 / 我卖出的订单
- 我的收藏
- 我发出的 / 我收到的留言
- 修改资料
- 修改密码

### 管理员后台

- 用户数量、商品数量、订单数量、成交金额、平均客单价
- 订单状态分布和最近订单
- 用户列表、搜索、停用/启用账号、设置/取消管理员
- 商品列表、搜索、状态筛选、查看已删除商品
- 下架违规商品、恢复上架
- 管理员不能停用自己，不能降级最后一个管理员

### 前端页面

| 页面 | 文件 |
| --- | --- |
| 首页 | `frontend/index.html` |
| 登录页 | `frontend/login.html` |
| 注册页 | `frontend/register.html` |
| 商品列表页 | `frontend/products.html` |
| 商品详情页 | `frontend/product.html` |
| 发布商品页 | `frontend/publish.html` |
| 编辑商品页 | `frontend/edit-product.html` |
| 我的收藏页 | `frontend/favorites.html` |
| 我的订单页 | `frontend/orders.html` |
| 我的商品页 | `frontend/my-products.html` |
| 个人中心页 | `frontend/profile.html` |
| 管理员后台页 | `frontend/admin.html` |
| 模拟支付页 | `frontend/payment.html` |

页面均为中文界面、响应式布局，包含加载状态、错误提示、表单校验、空数据提示和移动端导航。

---

## 二、技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.10+、FastAPI 0.115、Uvicorn |
| 数据库 | SQLite 3（标准库 `sqlite3`） |
| 模拟支付 | 本地沙盒网关，`payments` 支付流水表，不连接第三方 |
| 密码 | 标准库 `hashlib.pbkdf2_hmac`，310,000 次迭代，随机盐 |
| 会话 | 随机不透明 Token；数据库保存 SHA-256 摘要 |
| 前端 | 原生 HTML5、CSS3、JavaScript (ES2017+) |
| 测试 | pytest、FastAPI TestClient、unittest |
| 金额 | `decimal.Decimal`，统一保留两位小数 |

项目刻意没有引入 SQLAlchemy、Vue、Node 构建链、JWT 库或 `python-dotenv`，以降低安装和运行成本。运行依赖只有 FastAPI、Uvicorn；测试再加 pytest、httpx。

已验证环境：Python 3.12.14、Windows 11 / PowerShell。

---

## 三、项目结构

```text
student-discount-project/
├── backend/
│   ├── __init__.py           # 可选 .env 加载（无额外依赖）
│   ├── app.py                # FastAPI 入口、中间件、异常处理、静态页面挂载
│   ├── auth.py               # 密码哈希、Session Token、当前用户依赖
│   ├── database.py           # SQLite 连接、事务、初始化、路径解析
│   ├── deps.py               # FastAPI 数据库依赖
│   ├── models.py             # 建表 SQL、索引、领域常量
│   ├── money.py              # Decimal 金额工具，复用 checkout 折扣逻辑
│   ├── schemas.py            # Pydantic 请求校验模型
│   ├── serializers.py        # 数据库行 → 统一 JSON
│   ├── responses.py          # 统一成功/错误响应、ApiError
│   ├── seed.py               # 建库 + 种子数据 + 管理员创建
│   ├── routers/
│   │   ├── auth.py           # 注册、登录、退出、当前用户
│   │   ├── products.py       # 商品、收藏、留言
│   │   ├── orders.py         # 下单、模拟支付、订单列表、状态流转
│   │   ├── users.py          # 用户中心
│   │   └── admin.py          # 管理员统计与治理
│   └── tests/
│       ├── conftest.py
│       ├── helpers.py
│       ├── test_auth.py
│       ├── test_products.py
│       ├── test_favorites_messages.py
│       ├── test_orders.py
│       ├── test_payments.py
│       ├── test_admin.py
│       └── test_frontend_pages.py
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── products.html
│   ├── product.html
│   ├── publish.html
│   ├── edit-product.html
│   ├── favorites.html
│   ├── orders.html
│   ├── my-products.html
│   ├── profile.html
│   ├── admin.html
│   ├── payment.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js            # API 客户端、鉴权、Toast、卡片、分页等
│       ├── layout.js         # 全站页头、页脚、移动端菜单
│       └── pages/            # 各页面业务脚本
├── checkout.py               # 保留的原始学生折扣逻辑
├── test_checkout.py          # 保留的原始 5 项测试
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

---

## 四、安装步骤

### 1. 进入项目并创建虚拟环境

Windows PowerShell：

```powershell
cd "C:\Users\zard1\Desktop\协助示范软件开发\student-discount-project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 不允许执行激活脚本，可以不激活，后续始终使用 `.venv\Scripts\python.exe`：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

依赖清单：

```text
fastapi==0.115.14
uvicorn==0.34.3
pytest==8.4.2
httpx==0.28.1
```

### 3. 可选：配置环境变量

```powershell
Copy-Item .env.example .env
```

`.env` 已被 `.gitignore` 忽略，不会提交。常用配置：

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DATABASE_PATH` | SQLite 文件路径 | `backend/data/campus_market.db` |
| `ADMIN_USERNAME` | 可选，启动时自动创建的管理员用户名 | 空 |
| `ADMIN_PASSWORD` | 可选，管理员密码；不填则不自动创建 | 空 |
| `ADMIN_EMAIL` | 管理员邮箱 | `admin@campus.local` |
| `SESSION_TTL_HOURS` | 登录会话有效期 | `72` |
| `CORS_ORIGINS` | 单独启动前端时的允许来源 | 本地 8000 / 5500 |

> 不要把真实密码写入 `.env.example`、README 或代码。项目不包含任何硬编码密码或密钥。

---

## 五、数据库初始化

### 推荐方式：运行 seed 脚本

```powershell
python -m backend.seed
```

脚本会：

1. 自动创建 `backend/data/` 和 SQLite 数据库；
2. 创建全部表、索引和部分唯一索引；
3. 创建管理员账号；
4. 创建 3 个演示用户；
5. 写入 8 件演示商品、收藏、留言，以及一条已完成且带成功支付流水/交易号的学生折扣订单；
6. **在终端打印一次随机生成的初始密码**，不写入代码或文件。

演示账号：

| 用户名 | 身份 | 角色 |
| --- | --- | --- |
| `admin`（可通过 `ADMIN_USERNAME` 修改） | 非学生 | 管理员 |
| `campus_seller` | 学生 | 普通用户 |
| `campus_buyer` | 学生 | 普通用户 |
| `campus_visitor` | 非学生 | 普通用户 |

管理员密码和演示账号密码由脚本随机生成并打印。需要固定演示密码时：

```powershell
$env:ADMIN_PASSWORD = "请替换为强密码"
$env:DEMO_PASSWORD = "请替换为另一个强密码"
python -m backend.seed
```

也可以不运行 seed，直接在 `.env` 中配置 `ADMIN_USERNAME` / `ADMIN_PASSWORD`，后端启动时会自动创建管理员。

### 重置数据库

```powershell
python -m backend.seed --reset
```

`--reset` 会删除现有表并重建，**会丢失全部数据**，请谨慎使用。

### 直接启动

表结构会在应用启动时自动创建；即使没有运行 seed，也可以启动后端并注册普通用户，但不会有演示商品和管理员。

### 数据库表

| 表 | 作用 |
| --- | --- |
| `users` | 用户账号、密码哈希、学生身份、角色、资料、启用状态 |
| `sessions` | 登录会话，保存 Token 的 SHA-256 摘要和过期时间 |
| `products` | 商品、卖家、价格、分类、状态、软删除标记 |
| `favorites` | 用户收藏，`(user_id, product_id)` 唯一 |
| `messages` | 商品留言，关联商品和作者 |
| `orders` | 买家、卖家、商品、状态、原价/折扣/最终价快照、支付状态与交易号 |
| `payments` | 模拟支付流水：成功、失败、已退款记录 |

### 关系说明

```text
users 1 ─── N products        (seller_id)
users 1 ─── N sessions        (user_id)
users 1 ─── N favorites       (user_id)
users 1 ─── N messages        (user_id)
users 1 ─── N orders          (buyer_id / seller_id)
products 1 ─ N favorites      (product_id)
products 1 ─ N messages       (product_id)
products 1 ─ N orders         (product_id)
orders 1 ─── N payments       (order_id)
users 1 ─── N payments        (user_id)
```

关键约束：

- `favorites(user_id, product_id)` 唯一，防止重复收藏；
- `orders(product_id)` 上有一个**部分唯一索引**，只约束 `待确认 / 已确认 / 已完成` 的订单，取消后允许重新购买；
- 商品删除为软删除（`is_deleted = 1`），保护历史订单；
- 外键启用 `PRAGMA foreign_keys = ON`；
- 订单使用 `BEGIN IMMEDIATE` 事务和条件更新，降低并发重复购买风险；
- 订单价格以 TEXT 保存的两位小数字符串为准，避免浮点误差；
- `payments.transaction_no` 唯一，支付成功和失败都会生成沙盒流水；
- 订单支付状态为 `未支付 / 已支付 / 已退款`，只有已支付订单才能被卖家确认；
- 旧数据库启动时会执行轻量迁移，自动增加支付字段并回填历史订单。

建表 SQL 完整定义见 `backend/models.py` 的 `SCHEMA_SQL`，迁移逻辑见 `migrate_schema()`。

---

## 六、启动后端

```powershell
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

- 应用：<http://127.0.0.1:8000/>
- Swagger 文档：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>
- 健康检查：<http://127.0.0.1:8000/api/health>

前端由 FastAPI 的 `StaticFiles` 直接托管，**只需要启动后端**即可访问完整页面。

---

## 七、启动前端（两种方式）

### 方式 A：随 FastAPI 启动（推荐）

访问 <http://127.0.0.1:8000/> 即可，无需第二条命令。

### 方式 B：单独启动静态前端

在项目根目录另开一个终端：

```powershell
python -m http.server 5500 --directory frontend
```

访问 <http://127.0.0.1:5500/>。`frontend/js/api.js` 会自动把 5500 端口的 API 请求指向 `http://127.0.0.1:8000`，后端默认 CORS 已允许该来源。

如果换用其他端口，需要在 `.env` 的 `CORS_ORIGINS` 中加入对应来源，并重新启动后端。

---

## 八、默认账号说明

- 项目**没有硬编码的默认密码**。
- 管理员和演示账号由 `python -m backend.seed` 创建，密码随机生成并在终端显示一次。
- 管理员可通过 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 环境变量创建，也可通过 `--admin-password` 参数指定。
- 演示用户密码相同（`DEMO_PASSWORD` 或随机生成），仅用于本地课程演示。
- 如果密码遗失：
  - 删除 `backend/data/campus_market.db` 后重新 seed（会丢失数据）；或
  - 使用另一个 `ADMIN_USERNAME` 环境变量创建新的管理员；或
  - 在本地 sqlite 中直接更新 `users.password_hash`（需要使用项目的 PBKDF2 格式）。

密码规则：至少 8 个字符，必须同时包含字母和数字。

---

## 九、API 接口说明

### 统一响应格式

成功：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

失败：

```json
{
  "success": false,
  "message": "商品不存在",
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "details": null
  }
}
```

需要登录的接口使用请求头：

```http
Authorization: Bearer <token>
```

### 认证

| 方法 | 路径 | 登录 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 否 | 注册，成功后直接返回 Token |
| POST | `/api/auth/login` | 否 | 用户名或邮箱 + 密码登录 |
| POST | `/api/auth/logout` | 是 | 注销当前会话 |
| GET | `/api/auth/me` | 是 | 当前登录用户 |

注册示例：

```powershell
$body = @{
  username = "student_demo"
  email = "student@example.com"
  password = "Password123"
  display_name = "演示同学"
  is_student = $true
  campus = "主校区"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/auth/register `
  -ContentType "application/json" -Body $body
```

### 商品与收藏、留言

| 方法 | 路径 | 登录 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/products` | 可选 | 商品分页列表；登录时返回 `is_favorited` |
| POST | `/api/products` | 是 | 发布商品 |
| GET | `/api/products/categories` | 否 | 分类及数量、校区选项 |
| GET | `/api/products/{id}` | 可选 | 商品详情 |
| PUT | `/api/products/{id}` | 是 | 卖家编辑商品 |
| DELETE | `/api/products/{id}` | 是 | 卖家删除商品（软删除） |
| POST | `/api/products/{id}/favorite` | 是 | 收藏 |
| DELETE | `/api/products/{id}/favorite` | 是 | 取消收藏 |
| GET | `/api/products/{id}/messages` | 可选 | 商品留言列表 |
| POST | `/api/products/{id}/messages` | 是 | 发表留言 |
| DELETE | `/api/messages/{id}` | 是 | 作者或管理员删除留言 |

列表查询参数：

| 参数 | 说明 | 示例 |
| --- | --- | --- |
| `q` | 关键词，搜索名称/描述/分类 | `台灯` |
| `category` | 分类精确匹配 | `电子数码` |
| `campus` | 校区 | `主校区` |
| `min_price` / `max_price` | 价格区间 | `10` / `100` |
| `status` | `在售` / `已预订` / `已售出` | `在售` |
| `sort` | `newest` / `oldest` / `price_asc` / `price_desc` | `price_asc` |
| `page` | 页码，从 1 开始 | `1` |
| `page_size` | 每页 1-50 条 | `12` |

示例：

```text
GET /api/products?q=教材&category=教材书籍&min_price=10&max_price=60&sort=price_asc&page=1&page_size=12
```

分页返回：

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 12,
    "total": 0,
    "pages": 0
  }
}
```

### 订单

| 方法 | 路径 | 登录 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/orders` | 是 | 创建订单，body：`{"product_id": 1}` |
| GET | `/api/orders` | 是 | 我的订单，`role=all/buyer/seller`、`status`、分页 |
| GET | `/api/orders/{id}` | 是 | 订单详情，仅买卖双方或管理员 |
| GET | `/api/orders/{id}/payments` | 是 | 订单的模拟支付流水，仅买卖双方或管理员 |
| POST | `/api/orders/{id}/pay` | 是 | 买家发起模拟支付 |
| PUT | `/api/orders/{id}/status` | 是 | 更新状态，body：`{"status": "已确认"}` |

模拟支付请求：

```json
{
  "method": "mock_campus",
  "outcome": "success"
}
```

- `method`：`mock_campus`（校园卡）、`mock_card`（银行卡）、`mock_wallet`（校园钱包）；
- `outcome`：`success` 正常支付，`failure` 仅用于演示失败；失败返回 HTTP `402` 并记录失败流水；
- 支付成功返回沙盒交易号，如 `MOCK-20261112121246-D25A4BA5`；
- 不接收卡号、密码、验证码等任何真实支付凭证；
- 只有订单买家可以支付，只有已支付订单能被卖家确认。

状态流转：

| 当前状态 | 目标 | 允许操作者 | 前置条件 |
| --- | --- | --- | --- |
| 待确认 | 已确认 | 卖家、管理员 | 已支付 |
| 待确认 | 已取消 | 买家、卖家、管理员 | — |
| 已确认 | 已完成 | 买家、卖家、管理员 | 已支付 |
| 已确认 | 已取消 | 买家、卖家、管理员 | — |
| 已完成 / 已取消 | — | 终态，不可再变更 | — |

取消已支付订单时，系统会在同一事务中：

1. 将订单支付状态改为 `已退款`；
2. 记录退款金额和退款时间；
3. 将成功支付流水标记为 `已退款`；
4. 将商品恢复为 `在售`（若无其他进行中订单）。

下单时服务端会：

1. 校验商品为 `在售` 且不是自己的商品；
2. 用事务将商品改为 `已预订`；
3. 调用根目录 `checkout.py` 的 `calculate_total` 计算最终价；
4. 记录 `original_price`、`discount_amount`、`final_price`、`student_discount`；
5. 订单初始支付状态为 `未支付`，买家支付后卖家的“确认订单”按钮才可用。

学生订单示例：

```json
{
  "original_price": "19.99",
  "discount_amount": "2.00",
  "final_price": "17.99",
  "student_discount": true
}
```

非学生订单的 `final_price` 等于原价，`discount_amount` 为 `0.00`。

支付成功后的订单字段示例：

```json
{
  "payment": {
    "status": "已支付",
    "method": "mock_campus",
    "method_label": "校园卡（模拟）",
    "transaction_no": "MOCK-20261112121246-D25A4BA5",
    "paid_at": "2026-11-12T12:12:46+00:00",
    "refunded_at": null,
    "refund_amount": "0.00"
  }
}
```

### 用户中心

| 方法 | 路径 | 登录 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/users/me` | 是 | 个人资料 |
| PUT | `/api/users/me` | 是 | 修改昵称、校区、简介、头像、学生身份 |
| PUT | `/api/users/me/password` | 是 | 修改密码，保留当前会话并注销其他会话 |
| GET | `/api/users/me/products` | 是 | 我的商品，可按状态筛选 |
| GET | `/api/users/me/favorites` | 是 | 我的收藏，分页 |
| GET | `/api/users/me/messages` | 是 | `scope=authored` 我发出的，`received` 我收到的 |

### 管理员

| 方法 | 路径 | 登录 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/admin/statistics` | 管理员 | 用户/商品/订单/成交金额/状态分布/最近订单 |
| GET | `/api/admin/users` | 管理员 | 用户列表、搜索、分页 |
| PUT | `/api/admin/users/{id}` | 管理员 | 启用/停用、设置/取消管理员 |
| GET | `/api/admin/products` | 管理员 | 全部商品，含已下架/已删除 |
| PUT | `/api/admin/products/{id}/takedown` | 管理员 | 下架商品 |
| PUT | `/api/admin/products/{id}/restore` | 管理员 | 恢复上架 |

### 系统

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/overview` | 首页公开统计 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## 十、运行测试

### 完整测试

```powershell
python -m pytest -v
```

或使用项目虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### 只运行原始折扣测试

```powershell
python -m unittest -v test_checkout.py
```

或：

```powershell
python test_checkout.py
```

### 最近一次真实测试结果

测试命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

结果：

```text
62 passed, 1 warning in 21.34s
```

| 项目 | 数量 |
| --- | --- |
| 测试总数 | **62** |
| 通过 | **62** |
| 失败 | **0** |
| 警告 | 1 条（第三方 Starlette TestClient 的 `anyio` 弃用提示，不影响功能） |

测试分布：

| 测试文件 | 覆盖内容 |
| --- | --- |
| `test_checkout.py` | 学生 9 折、非学生原价、四舍五入、负数校验、兼容函数（5 项） |
| `backend/tests/test_auth.py` | 注册、重复用户名/邮箱、密码哈希、登录、错误密码、鉴权、退出、资料和密码修改（9 项） |
| `backend/tests/test_products.py` | 发布、搜索、分类、价格、排序、分页、详情、编辑、删除、越权、校验（7 项） |
| `backend/tests/test_favorites_messages.py` | 收藏、取消、我的收藏、留言、卖家查看、删除权限、登录要求（5 项） |
| `backend/tests/test_orders.py` | 学生折扣、非学生原价、重复购买、自购限制、确认/完成、取消回滚、权限、订单列表（9 项） |
| `backend/tests/test_payments.py` | 模拟支付成功、未支付拦截确认、买家权限、重复支付、失败重试、取消退款、支付校验与流水权限（7 项） |
| `backend/tests/test_admin.py` | 管理员权限、统计、用户管理、自我停用保护、商品下架/恢复、已售商品恢复、删除留言（7 项） |
| `backend/tests/test_frontend_pages.py` | 13 个页面均可通过 HTTP 访问（参数化 13 项） |

### 本次额外浏览器验证（不在 pytest 套件内）

除自动化测试外，开发过程中使用 Chrome Headless + CDP 实际验证了：

- 桌面端 1440px 和移动端 390px 首页无横向溢出；
- 真实登录表单登录管理员；
- 真实发布表单创建商品并跳转详情；
- 学生买家收藏、发送留言、下单；
- 订单页显示学生 9 折金额（`66.60 → 59.94`）；
- 模拟支付页成功支付 `¥25.20`，生成 `MOCK-...` 交易号并显示成功回执；
- 订单页显示“待确认 + 已支付”，已支付订单无重复支付入口；
- 模拟支付失败后订单保持未支付、显示错误并可重试；
- 管理员后台统计卡片、用户表和商品表正常渲染；
- 浏览器运行时无 JavaScript 异常（部分 Unsplash 外链图片被浏览器网络策略拦截时会显示占位图，不影响业务）。

这些浏览器步骤没有加入仓库内的 CI 测试，仓库中的自动化测试仍然是 62 项 API/页面可达性测试。

### 未测试 / 未实现内容

- 未接入真实支付平台（支付宝/微信/Stripe）、真实退款、Webhook、支付回调验签、对账和发票；
- 当前“支付成功/退款”仅写入本地 SQLite 的模拟流水，不具备任何真实支付效力；
- 未接入学信网/校园统一身份认证，学生身份是演示字段；
- 未实现邮件验证、短信验证、找回密码；
- 未把浏览器端 E2E（Playwright/Cypress）纳入自动化测试和多浏览器兼容矩阵；本次只用 Chrome Headless 做了手动脚本验证；
- 未做高并发压力测试和 SQLite 多进程写入压测；
- 未实现图片上传，当前只保存图片 URL；
- 未实现实时聊天、站内通知、举报审核流；
- 未实现 CSRF/刷新 Token/设备管理；
- 前端 Token 保存在 `localStorage`，这是课程演示的简化做法，生产环境建议改用 HttpOnly Cookie 并配合 CSRF 防护。

---

## 十一、Git 分支开发说明

当前主分支：`main`

建议每个功能使用独立分支，通过 Pull Request 合并：

```powershell
git switch main
git pull origin main
git switch -c feature/campus-market

git status
git add backend frontend README.md requirements.txt .env.example .gitignore pytest.ini
git commit -m "feat: build campus second-hand marketplace"

git push -u origin feature/campus-market
```

然后在 GitHub 创建 Pull Request，检查测试通过后合并到 `main`。

提交前检查：

```powershell
git status --short
git diff --check
python -m pytest -q
```

不要提交：

- `.env` 或任何真实密码、Token、密钥；
- `backend/data/*.db` 数据库文件；
- `.venv/`、`__pycache__/`、`.pytest_cache/`。

`.gitignore` 已覆盖这些路径。

本项目保留了原仓库的 Git 历史和 `checkout.py`、`test_checkout.py`，未删除原有功能。

---

## 十二、安全设计说明

- 密码：PBKDF2-HMAC-SHA256，310,000 次迭代，16 字节随机盐；
- Token：`secrets.token_urlsafe(32)` 生成，数据库只存 SHA-256 摘要；
- 退出登录删除当前 Session；
- 停用用户删除全部 Session；
- 修改密码注销其他设备会话；
- 所有 SQL 使用参数化查询，不拼接用户输入；
- 所有写接口校验登录状态和资源归属；
- 订单价格完全由服务端计算，客户端不能提交金额；
- 模拟支付金额直接取订单 `final_price`，客户端不能提交金额；
- 只有订单买家可以支付，只有已支付订单可以被卖家确认；
- 支付成功后订单支付状态与支付流水在同一事务中写入；
- 模拟网关不接收卡号、密码、验证码等真实支付凭证；
- 商品删除采用软删除，保护历史订单；
- 前端对输出做 HTML 转义，图片 URL 仅允许 http(s) 或站内路径；
- 统一异常处理，不向前端泄漏堆栈或数据库细节；
- 响应增加 `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy` 等基础安全头。

尚未实现（生产环境需补）：登录限流、验证码、审计日志、HTTPS、密钥轮换、CSRF、CSP、备份策略。

---

## 十三、常见问题

### 1. `python` 找不到或没有 pip

使用项目虚拟环境中的解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload
```

如果创建虚拟环境失败，先安装 Python 3.10+ 并勾选 “Add Python to PATH”。

### 2. PowerShell 提示无法加载 `Activate.ps1`

可以直接绕过激活脚本，始终使用 `.venv\Scripts\python.exe`；或临时执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 3. 端口 8000 被占用

换一个端口：

```powershell
python -m uvicorn backend.app:app --reload --port 8001
```

或查看占用：

```powershell
Get-NetTCPConnection -LocalPort 8000
```

### 4. 数据库想重新开始

```powershell
python -m backend.seed --reset
```

或停止后端后删除 `backend/data/campus_market.db`，再运行 `python -m backend.seed`。

### 5. 管理员密码忘了

seed 不会重置已存在账号的密码。可以删除数据库重建，或配置另一个管理员用户名：

```powershell
$env:ADMIN_USERNAME = "admin_backup"
$env:ADMIN_PASSWORD = "请替换为强密码"
python -m backend.seed
```

### 6. 前端单独打开时请求失败 / CORS

确认后端在 `127.0.0.1:8000` 运行；确认前端从 `5500` 端口访问；检查 `.env` 的 `CORS_ORIGINS` 是否包含对应来源。直接访问 `http://127.0.0.1:8000/` 最省事。

### 7. 商品图片不显示

演示数据使用 Unsplash 外链，离线环境可能加载失败，页面会自动显示占位图。也可以在发布/编辑时填写自己的图片 URL。

### 8. 测试时提示 `PermissionError` / 无法创建数据库

测试默认在项目根目录的 `.test-data/` 中创建临时 SQLite 文件，需要当前用户对项目目录有写权限。不要在网络盘只读目录中运行测试。

### 9. 下单提示“已有有效订单”

同一商品只允许一条有效订单。卖家取消或买家取消后商品会回到在售，其他买家才能重新下单。

### 10. 为什么学生价和页面预估不同

页面上的学生价只是展示估算，最终金额以下单接口返回的 `final_price` 为准；服务端复用 `checkout.calculate_total` 并使用 `ROUND_HALF_UP` 保留两位小数。

### 11. 模拟支付失败怎么办

支付页的“模拟支付失败（测试）”按钮故意触发失败分支，订单会保持 `未支付`，失败流水会保留。重新选择支付方式并点击“确认模拟支付”即可重试；同一个订单支付成功后不能重复支付。

### 12. 是否真的会扣款

不会。模拟支付只写入本地 SQLite 的 `payments` 表，不连接任何银行或第三方支付平台，也不接收真实卡号、密码或验证码。

---

## 十四、后续可扩展功能

- 接入 Stripe/支付宝/微信沙箱，增加 Webhook 验签、支付回调、幂等对账和真实退款
- 图片上传（本地存储或对象存储）与多图相册
- 校园统一身份认证 / 学号验证，替代手动学生身份字段
- 站内实时聊天、消息通知、邮件提醒
- 举报、审核队列、管理员操作审计日志
- 订单收货地址、面交二维码、评价与信用分
- 收藏降价提醒、关键词订阅
- 管理后台图表（趋势、分类、校区分布）与 CSV 导出
- 登录限流、验证码、刷新 Token、HttpOnly Cookie + CSRF
- Docker Compose、PostgreSQL、Alembic 迁移
- Playwright 端到端测试与 CI（GitHub Actions）
- 响应式图片、骨架屏优化、无障碍审计

---

## 十五、原始学生折扣练习

根目录的 `checkout.py` 保持原有行为：

```python
from decimal import Decimal
from checkout import calculate_total

calculate_total("100.00", True)   # Decimal("90.00")
calculate_total("100.00", False)  # Decimal("100.00")
calculate_total("19.99", True)    # Decimal("17.99")
```

`backend/money.py` 的 `price_breakdown()` 直接导入并调用 `calculate_total`，订单结算没有复制一套折扣算法。原有 `test_checkout.py` 的 5 项测试仍然全部通过。

---

## License

本项目为课程练习代码，未声明生产级授权与合规承诺。使用第三方图片 URL 时请遵守对应网站的服务条款。
