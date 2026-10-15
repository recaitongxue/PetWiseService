# Petwise 服务端接口文档

> **版本** v1.1 · **基础路径** `/api/v1` · **最后更新** 2026-10-14
>
> 本文档依据 `apps/mobile/src/data/mock.js`（静态数据）与 `apps/mobile/src/data/ops.js`（本地持久化层）的实际数据契约编写，
> 凡本文档定义的字段名，前端均已有对应消费代码，**按此实现即可无缝替换 Mucf 为真实接口**。
> 前端改造时的对应关系见 [附录 B：Mucf → API 替换映射表](#附录-bmock--api-替换映射表)。

---

## 目录

- [1. 通用约定](#1-通用约定)
- [2. 鉴权方案](#2-鉴权方案)
- [3. 数据模型与表结构](#3-数据模型与表结构)
- [4. 接口明细](#4-接口明细)
  - [4.1 认证与用户](#41-认证与用户)
  - [4.2 宠物档案](#42-宠物档案)
  - [4.3 健康记录与体重](#43-健康记录与体重)
  - [4.4 日程与提醒](#44-日程与提醒)
  - [4.5 首页聚合](#45-首页聚合)
  - [4.6 公告与反馈](#46-公告与反馈)
  - [4.7 拍照识别](#47-拍照识别)
  - [4.8 品种百科](#48-品种百科)
  - [4.9 问诊：元信息与词典](#49-问诊元信息与词典)
  - [4.10 问诊：AI 分诊与额度](#410-问诊ai-分诊与额度)
  - [4.11 问诊：医生](#411-问诊医生)
  - [4.12 问诊：问诊单与实时消息](#412-问诊问诊单与实时消息)
  - [4.13 问诊：评价与报告](#413-问诊评价与报告)
- [4.14 社区](#414-社区)
- [4.15 即时消息 IM](#415-即时消息-im)
- [4.16 收藏](#416-收藏)
- [4.17 文件上传](#417-文件上传)
- [4.18 管理端](#418-管理端)
- [4.19 钱包](#419-钱包)
- [5. WebSocket 实时协议](#5-websocket-实时协议)
- [6. 附录](#6-附录)

---

## 1. 通用约定

### 1.1 基础信息

| 项 | 值 |
| --- | --- |
| 基础路径 | `https://{host}/api/v1` |
| 协议 | HTTPS（生产）/ HTTP（本地开发） |
| 请求格式 | `application/json`（文件上传除外） |
| 字符编码 | UTF-8 |
| 时间格式 | 日期 `YYYY-MM-DD`；时刻 `YYYY-MM-DD HH:mm:ss` 或 ISO 8601 |
| 金额单位 | 元（人民币），保留 2 位小数 |

### 1.2 统一响应包

所有接口（含错误）统一使用如下信封，**HTTP 状态码表达结果类别，`code` 表达业务结果**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "timestamp": 1760000000000,
  "traceId": "req_8f3a1b2c"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | `0` 表示成功，非 0 为业务错误码，见 [1.4](#14-错误码) |
| `message` | string | 面向开发/用户的可读提示，前端 toast 可直接展示 |
| `data` | any | 业务数据，失败时为 `null` |
| `timestamp` | long | 服务端毫秒时间戳 |
| `traceId` | string | 链路追踪 ID，用于日志定位 |

### 1.3 分页结构

分页查询统一使用 `page` / `pageSize` 入参，返回 `Page<T>`：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [],
    "total": 128,
    "page": 1,
    "pageSize": 20,
    "hasMore": true
  }
}
```

> 说明：列表中若存在被安全过滤或删除的内容，服务端应直接剔除，前端不做二次过滤。

### 1.4 错误码

HTTP 状态码与业务 `code` 分段对应，**前端按 `code` 分支处理，不依赖 `message` 文案**。

| HTTP | code | 含义 | 前端处理建议 |
| --- | --- | --- | --- |
| 200 | 0 | 成功 | — |
| 400 | 10001 | 参数错误（缺参/类型错误） | 提示 `message` |
| 400 | 10002 | 参数校验失败 | `details` 逐字段高亮 |
| 401 | 20001 | 未登录 / token 缺失 | 跳转登录页 |
| 401 | 20002 | token 过期 | 静默刷新后重试，失败则跳登录 |
| 401 | 20003 | token 无效（被踢/签名错误） | 清登录态并跳登录 |
| 403 | 20004 | 无权限 | 提示无权限 |
| 404 | 30001 | 资源不存在 | 提示或展示空态 |
| 409 | 30002 | 资源冲突（如重复登记） | 提示 `message` |
| 429 | 40001 | 请求过于频繁 | 提示稍后再试 |
| 429 | 41001 | **AI 免费额度已用尽** | 引导转真人医生 |
| 422 | 42001 | 问诊单状态不允许该操作 | 提示 `message` |
| 500 | 50000 | 服务内部错误 | 通用错误页 |

带校验详情的响应：

```json
{
  "code": 10002,
  "message": "参数校验失败",
  "data": {
    "details": [
      { "field": "phone", "issue": "手机号格式不正确" },
      { "field": "text", "issue": "描述不能为空" }
    ]
  },
  "timestamp": 1760000000000,
  "traceId": "req_8f3a1b2c"
}
```

### 1.5 通用请求头

| 头 | 必填 | 说明 |
| --- | --- | --- |
| `Authorization` | 是（除登录接口） | `Bearer {accessToken}` |
| `Content-Type` | 是 | `application/json`；上传为 `multipart/form-data` |
| `X-Client` | 否 | `app` / `admin`，多端差异时使用 |
| `Idempotency-Key` | 否 | 下单类 POST 建议携带，防重复提交 |

### 1.6 约定细则

1. **资源命名**：复数名词，如 `/pets`、`/consult/orders`；不使用动词。
2. **幂等性**：创建订单、发送消息建议支持 `Idempotency-Key`，重复请求返回首次结果。
3. **软删除**：用户内容删除采用软删（`deletedAt`），列表不再返回。
4. **金额**：服务端计算并返回，前端不参与计价，避免被篡改。
5. **敏感信息**：禁止在 `message` 中回显堆栈、SQL、内网地址。
6. **限流**：登录与验证码接口按 IP + 手机号限流，AI 分诊接口按用户日配额限流。

---

## 2. 鉴权方案

采用 **短效 JWT + 长效 Refresh Token** 双令牌方案（业界主流做法）。

```text
┌────────┐                        ┌────────┐
│ Client │  POST /auth/login      │ Server │
│        │ ─────────────────────► │        │
│        │  ◄─────────────────────│        │  accessToken(2h) + refreshToken(30d)
│        │  GET /pets             │        │
│        │ ──────Bearer─────────► │        │
│        │  ◄─────────────────────│        │
│        │  (20002 过期)          │        │
│        │  POST /auth/refresh    │        │
│        │ ─────────────────────► │        │
│        │  ◄─────────────────────│        │  新 accessToken
└────────┘                        └────────┘
```

| 令牌 | 有效期 | 存储位置 | 载荷 |
| --- | --- | --- | --- |
| `accessToken` | 2 小时 | 内存 / localStorage | `sub`(userId) `phone` `role` `exp` |
| `refreshToken` | 30 天 | 服务端 Redis + 客户端安全存储 | `sub` `jti` `exp` |

规则：

- 除 `/auth/**`、公开读接口（品种百科、在线医生列表）外，均需 `Authorization`。
- `accessToken` 过期返回 `code=20002`，前端应**携带同一请求重试一次**，不应直接登出。
- 修改密码、登出时使 `refreshToken` 失效。
- 管理端使用 `role=admin` 令牌，管理接口需校验该角色。

---

## 3. 数据模型与表结构

### 3.1 实体关系概览

```text
user ──┬─< pet ──┬─< pet_weight_record
       │         ├─< health_record
       │         ├─< schedule_item
       │         ├─< consult_order ──< consult_message
       │         └─< consult_report
       ├─< favorite
       ├─< post ──< comment / post_like
       ├─< conversation ──< message
       ├─< ai_usage_daily
       └─< recognition_record

doctor ──< consult_order
       ──< doctor_review
announcement / feedback  ← 管理端维护
breed (字典表)
```

### 3.2 表结构建议

> 类型以 MySQL 8 为例；所有表含 `id` 主键、`created_at`、`updated_at`，软删除字段视业务而定。

#### `user` 用户

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | 用户 ID |
| `phone` | varchar(20) UNIQUE | 手机号（登录账号） |
| `password_hash` | varchar(128) NULL | 密码哈希（支持密码登录时启用） |
| `nickname` | varchar(32) | 昵称，对应前端 `user.name` |
| `handle` | varchar(32) | 个性标识，如 `@manman` |
| `avatar_url` | varchar(255) | 头像 URL（为空时前端用首字花押） |
| `bio` | varchar(120) | 简介 |
| `followers` / `following` | int | 关注数（可由关系表统计，冗余便于展示） |
| `role` | tinyint | 0 普通用户 / 1 医生 / 2 管理员 |
| `status` | tinyint | 1 正常 / 0 禁用 |

#### `pet` 宠物

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | 宠物 ID |
| `user_id` | bigint | 所属用户 |
| `name` | varchar(32) | 昵称 |
| `species` | varchar(16) | `cat` / `dog` / `other` |
| `breed` | varchar(64) | 品种名称（文本冗余） |
| `breed_id` | bigint NULL | 关联品种百科 |
| `gender` | varchar(4) | 公 / 母 |
| `birthday` | date | 出生日期 |
| `age` | decimal(3,1) | 年龄（岁，可由 birthday 计算） |
| `weight` | decimal(5,2) | 当前体重 kg |
| `tagline` | varchar(64) | 心情签名 |
| `health_score` | tinyint | 健康评分 0–100 |
| `next_vaccine` | date | 下次疫苗日期 |
| `avatar_url` | varchar(255) | 头像 |

#### `pet_weight_record` 体重记录

`id` / `pet_id` / `weight` decimal(5,2) / `recorded_at` date / `source` tinyint（1 手动 2 问诊回流）

#### `health_record` 健康记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `pet_id` | bigint | |
| `kind` | varchar(16) | `weight` 体重 / `diet` 饮食 / `symptom` 症状 / `care` 护理 |
| `date` | date | 记录日期 |
| `value` | decimal(5,2) NULL | 数值型记录（如体重） |
| `note` | varchar(500) | 文字描述 |
| `source` | tinyint | 1 用户录入 / 2 问诊报告回流 |
| `ref_id` | bigint NULL | 关联 report_id |

#### `health_trend` 健康趋势（每日）

`id` / `pet_id` / `day` tinyint(1-7) / `value` tinyint / `label` varchar(8) / `stat_date` date
> 用于首页周健康环形图；也可由日报数据实时聚合。

#### `schedule_item` 日程

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `pet_id` | bigint NULL | 为空表示通用日程 |
| `user_id` | bigint | |
| `title` | varchar(64) | 标题 |
| `type` | varchar(16) | `vaccine`/`deworm`/`check`/`weight`/`groom`/`other` |
| `date` | date | 计划日期 |
| `cycle` | varchar(32) | 周期说明，如「每季度一次」 |
| `custom` | tinyint | 1 用户自建 / 0 系统周期生成 |
| `done` | tinyint | 完成状态 |

> 完成状态也可用独立表 `schedule_done(pet_id, item_id, user_id)`。当前前端按 ID 集合存储，建议服务端返回时展开为 `done` 字段。

#### `announcement` 公告（管理端维护）

`id` / `title` / `body` / `level` varchar(16)（`event` 活动 / `warn` 警示 / `info` 通知）/ `active` tinyint / `publish_date` date

#### `announcement_dismiss` 公告关闭记录

`user_id` / `announcement_id` / 联合唯一，用于「用户已读不再展示」。

#### `feedback` 意见反馈

`id` / `user_id` / `type` varchar(16) / `text` varchar(1000) / `state` varchar(16)（`open` / `processing` / `resolved`）/ `created_at`

#### `recognition_record` 识别记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `user_id` / `pet_id` | bigint | |
| `image_url` | varchar(255) | 原图 |
| `result_title` | varchar(64) | 识别结果标题（如「英国短毛猫」） |
| `sci_name` | varchar(64) | 学名 |
| `confidence` | decimal(4,3) | 置信度 0–1 |
| `species` | varchar(16) | |
| `metrics` | json | `[{label,value,state}]` |
| `note` | varchar(500) | 综合提示 |

#### `breed` 品种百科

`id` / `name` / `sci_name` / `species` / `origin` / `temperament` json / `weight_range` / `life_span` / `health_issues` json / `care_guide` text / `cover_url`

#### `doctor` 医生

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `name` / `title` / `dept` / `dept_label` / `hospital` | varchar | 基础信息 |
| `years` | int | 从业年限 |
| `rating` | decimal(2,1) | 综合评分 |
| `consults` | int | 接诊量 |
| `online` | tinyint | 在线状态（建议由 Redis 心跳维护） |
| `response_min` | int | 平均响应分钟 |
| `tags` / `good_at` | json | 擅长标签数组 |
| `intro` | varchar(500) | 简介 |
| `certs` | json | 资质证书数组 |
| `slot` | varchar(64) | 排班展示文本 |
| `avatar_url` | varchar(255) | |

#### `doctor_review` 医生评价

`id` / `doctor_id` / `order_id` / `user_id` / `score` tinyint / `tags` json / `created_at`

#### `consult_order` 问诊单

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `user_id` / `pet_id` / `doctor_id` | bigint | |
| `mode` | varchar(16) | `text` 图文 / `voice` 电话 / `video` 视频 |
| `price` | decimal(8,2) | 实付金额 |
| `state` | varchar(16) | `pending` 待接诊 → `replied` 已回复 → `closed` 已结束 |
| `summary` | json | AI 生成的病例摘要 |
| `created_at` / `closed_at` | datetime | |

#### `consult_message` 问诊消息

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `order_id` | bigint | |
| `type` | varchar(16) | `user` / `doctor` / `system` / `rx`（处方卡） |
| `text` | text | 文本内容 |
| `images` | json | 图片 URL 数组 |
| `drugs` | json | 处方药品（type=rx 时） |
| `created_at` | datetime | |

#### `consult_report` 问诊报告

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint PK | |
| `type` | varchar(16) | `ai` 结构化预问诊 / `human` 真人问诊 |
| `user_id` / `pet_id` / `order_id` | bigint | 真人问诊关联订单 |
| `title` / `preview` | varchar | 列表展示用 |
| `chief` | json | 结构化主诉 |
| `triage` | json | 分诊结论（含 `level`/`score`/`factors`/`causes`/`actions`） |
| `doctor` | json | 医生信息（type=human） |
| `doctor_advice` | text | 医生建议 |
| `rx` | json | 处方 `{drugs:[], note}` |
| `archived` | tinyint | 是否已回流健康档案 |
| `reminded` | tinyint | 是否已生成日程提醒 |
| `date` | date | 报告日期 |

#### `ai_usage_daily` AI 额度

`user_id` / `stat_date` date / `used` int / 联合唯一；每日免费额度常量服务端配置（当前为 3）。

#### `post` 社区帖子

`id` / `user_id` / `author` / `role` varchar(16)（`vet` 认证兽医）/ `text` / `images` json / `tags` json / `likes` int / `comments` int / `created_at`

#### `post_like` / `comment` / `conversation` / `message` / `favorite`

均为常规结构，`favorite` 支持 `target_type`（`breed`/`post`/`tip`）+ `target_id`。

---

## 4. 接口明细

图例：`●` 需要登录，`○` 不需要登录。

### 4.1 认证与用户

#### 4.1.1 发送验证码 `○`

`POST /auth/verification-codes`

> 演示环境前端未真实调用，接入后端后由真实的短信网关下发。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `phone` | string | 是 | 11 位手机号，正则 `^1[3-9]\d{9}$` |
| `scene` | string | 否 | `login` / `register` / `reset`，默认 `login` |

```json
{ "phone": "13800001111", "scene": "login" }
```

**响应**

```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": {
    "phoneMasked": "138****1111",
    "expiresIn": 60,
    "cooldown": 60
  }
}
```

**频控与安全（服务端强制）**

| 规则 | 值 | 超限响应 |
| --- | --- | --- |
| 单手机号发送间隔 | 60s（`cooldown`） | `code=42901` |
| 单手机号每日发送上限 | 5 条/自然日 | `code=42902` |
| 单 IP 每小时发送上限 | 20 条 | `code=42903` |
| 验证码有效期 | 5 分钟 | 过期 `code=41001` |
| 验证码错误尝试 | 5 次后作废 | `code=41002` |

> 前端演示实现同步上述策略：60s 冷却 + 每日 5 次上限（`petwise_sms_sent` 按日计数），超限禁用按钮并提示。
> 生产环境**禁止**在响应中返回验证码本身。本地/联调阶段可通过服务端配置开关返回 `debugCode` 字段。

#### 4.1.2 验证码登录 `○`

`POST /auth/login`

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `phone` | string | 是 | 手机号 |
| `code` | string | 是 | 验证码 |
| `mode` | string | 否 | `sms` / `password`，默认 `sms` |
| `password` | string | 条件 | `mode=password` 时必填 |

**响应**

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "rt_9f2c...",
    "expiresIn": 7200,
    "user": {
      "id": "10001",
      "phone": "13800001111",
      "phoneMasked": "138****1111",
      "name": "林小满",
      "handle": "@manman",
      "avatarUrl": null,
      "bio": "两只猫的铲屎官 · 关注宠物健康",
      "followers": 328,
      "following": 156
    }
  }
}
```

#### 4.1.3 刷新令牌 `○`

`POST /auth/refresh`

```json
{ "refreshToken": "rt_9f2c..." }
```

响应同 `data` 中的令牌部分（`accessToken` / `refreshToken` / `expiresIn`）。失败返回 `code=20003`，前端应清除登录态并跳转登录页。

#### 4.1.4 登出 `●`

`POST /auth/logout`

服务端使当前 `refreshToken` 失效。响应 `data: null`。前端同时清除本地登录态。

#### 4.1.5 获取当前用户 `●`

`GET /users/me`

返回同 4.1.2 中的 `user` 对象。

#### 4.1.6 更新用户资料 `●`

`PATCH /users/me`

支持字段：`name`、`handle`、`avatarUrl`、`bio`。返回更新后的 `user`。

#### 4.1.7 修改密码 `●`

`PUT /users/me/password`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `oldPassword` | string | 是 | 原密码，≥6 位 |
| `newPassword` | string | 是 | 新密码，≥6 位，不得与原密码相同 |

成功返回 `204` 并使该用户**其它端的 refreshToken 全部失效**（强制重新登录）。
前端校验与后端一致：原密码错误 `code=41003`、新旧相同 `code=42203`。

#### 4.1.8 更换手机号 `●`

`POST /users/me/phone`，请求 `{ "newPhone": "13987654321", "smsCode": "654321" }`。

> `smsCode` 走 §4.1.1 发送（`scene=change-phone`）。成功返回新 token 对，旧手机号立即失效。

#### 4.1.9 账号偏好与隐私设置 `●`

`GET /users/me/preferences` / `PATCH /users/me/preferences`

```json
{
  "personalized": true,
  "visibility": "public",
  "binds": { "wechat": true, "apple": false }
}
```

| 字段 | 说明 |
| --- | --- |
| `personalized` | 个性化推荐开关（《互联网信息服务算法推荐管理规定》要求提供关闭项） |
| `visibility` | 社区动态可见范围：`public` / `followers` / `private` |
| `binds` | 第三方绑定状态；解绑/绑定走 `POST /users/me/bindings/{provider}` |

#### 4.1.10 黑名单 `●`

`GET /users/me/blocked` / `DELETE /users/me/blocked/{userId}`

黑名单用户不可关注、评论、私信本账号。

#### 4.1.11 注销账号 `●`

注销流程与主流平台对齐（条件检查 → 风险确认 → 短信验证 → 冷静期）：

1. **条件检查** `GET /users/me/delete-checks` →
   `{ "checks": [{ "label": "钱包余额已清零", "ok": false, "hint": "当前余额 ¥68.50" }], "ready": false }`
   后端校验：余额为零、无进行中问诊单、无未结算资产、账号无安全风险
2. **提交申请** `POST /users/me/deletion`，body `{ "reason": "privacy", "smsCode": "..." }` →
   `{ "cooldownEndsAt": "2026-10-21T00:00:00+08:00" }`；提交后强制下线
3. **冷静期**：默认 7 天（微信 60 天 / 淘宝 15 天量级，按合规与产品取值）；期间**任何登录自动撤销申请**
4. **撤销** `DELETE /users/me/deletion` → 账号立即恢复
5. 冷静期结束：数据匿名化后物理删除（宠物档案/问诊记录/社区内容/钱包流水），仅保留法律要求的留存项

> 前端演示环境：`Account.vue` 完整实现四步流程，「退出并清除本机数据」清除全部 `petwise_*` 本地键。

---

### 4.2 宠物档案

#### 4.2.1 宠物列表 `●`

`GET /pets`

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "mochi",
      "name": "麻薯",
      "species": "cat",
      "breed": "英国短毛猫",
      "age": 3,
      "weight": 4.6,
      "gender": "母",
      "tagline": "今日心情：慵懒",
      "healthScore": 86,
      "nextVaccine": "2026-11-02",
      "birthday": "2023-04-18",
      "avatarUrl": null
    }
  ]
}
```

> 前端「我与多宠切换」依赖该列表，返回顺序即展示顺序。

#### 4.2.2 宠物详情 `●`

`GET /pets/{id}`

除基础字段外，额外返回概要统计（用于档案页头部）：

```json
{
  "data": {
    "id": "mochi",
    "name": "麻薯",
    "healthScore": 86,
    "weightTrend": "up",
    "recordCount": 12,
    "pendingSchedule": 3
  }
}
```

#### 4.2.3 新建宠物 `●`

`POST /pets`

请求字段：`name`、`species`、`breed`、`gender`、`birthday`、`weight`、`tagline`。
返回完整宠物对象，`201`。

#### 4.2.4 更新 / 删除宠物 `●`

`PATCH /pets/{id}` · `DELETE /pets/{id}`（删除返回 `204`）

#### 4.2.5 周健康趋势 `●`

`GET /pets/{id}/health-trend?week=2026-41`

```json
{
  "data": {
    "petId": "mochi",
    "week": "2026-41",
    "points": [
      { "day": "一", "value": 92, "label": "优" },
      { "day": "二", "value": 88, "label": "良" },
      { "day": "三", "value": 74, "label": "需关注" },
      { "day": "四", "value": 90, "label": "优" },
      { "day": "五", "value": 95, "label": "优" },
      { "day": "六", "value": 83, "label": "良" },
      { "day": "日", "value": 86, "label": "良" }
    ]
  }
}
```

> `label` 由服务端按评分区间给出（`优` / `良` / `需关注`），保证多端一致。

#### 4.2.6 宠物当日提醒 `●`

`GET /pets/{id}/reminders?date=2026-10-11`

```json
{
  "data": [
    { "id": "rm1", "icon": "calendar-check", "label": "年度疫苗", "date": "11-02", "state": "watch" },
    { "id": "rm2", "icon": "pill", "label": "体内驱虫", "date": "10-20", "state": "good" }
  ]
}
```

`state`：`good` 正常 / `watch` 临近需关注 / `overdue` 已逾期。`icon` 沿用前端图标字典名，见 [附录 A](#附录-a枚举字典)。

---

### 4.3 健康记录与体重

#### 4.3.1 体重历史 `●`

`GET /pets/{id}/weights?months=6`

```json
{
  "data": [
    { "m": "5月", "w": 4.1 },
    { "m": "6月", "w": 4.3 },
    { "m": "7月", "w": 4.4 },
    { "m": "8月", "w": 4.5 },
    { "m": "9月", "w": 4.6 },
    { "m": "10月", "w": 4.6 }
  ]
}
```

> 同一自然月存在多条时取**最新一条**（前端图表去重逻辑依赖此约定）。

#### 4.3.2 记录体重 `●`

`POST /pets/{id}/weights`

```json
{ "weight": 4.7, "date": "2026-10-11" }
```

响应返回最新体重对象，并同步更新 `pet.weight`。

#### 4.3.3 健康记录列表 `●`

`GET /pets/{id}/records?kind=&page=1&pageSize=20`

```json
{
  "data": {
    "list": [
      {
        "id": "r1",
        "kind": "weight",
        "date": "2026-10-11",
        "value": 4.7,
        "note": "早晨空腹称重",
        "source": 1
      }
    ],
    "total": 12,
    "page": 1,
    "pageSize": 20,
    "hasMore": false
  }
}
```

`kind` 取值与图标展示：

| kind | 中文 | 前端图标 |
| --- | --- | --- |
| `weight` | 体重 | `scale` |
| `diet` | 饮食 | `heart` |
| `symptom` | 症状 | `firstaid` |
| `care` | 护理 | `sparkle` |

#### 4.3.4 新增健康记录 `●`

`POST /pets/{id}/records`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `kind` | string | 是 | 见上表 |
| `date` | string | 是 | `YYYY-MM-DD` |
| `value` | number | 否 | 体重类记录必填 |
| `note` | string | 否 | 备注，≤500 字 |

#### 4.3.5 删除健康记录 `●`

`DELETE /records/{id}` → `204`

---

### 4.4 日程与提醒

#### 4.4.1 日程列表 `●`

`GET /schedule?petId=&from=&to=&type=`

返回**系统按免驱/疫苗周期自动生成**的日程 + 用户自建日程的合并结果：

```json
{
  "data": [
    {
      "id": "m1",
      "petId": "mochi",
      "date": "2026-10-18",
      "title": "体外驱虫",
      "type": "deworm",
      "cycle": "每月一次",
      "custom": false,
      "done": false,
      "state": "soon"
    }
  ]
}
```

`state` 由服务端按当前日期计算：`overdue` 已逾期 / `today` 今日 / `soon` 即将（7 天内）/ `future` 未来。

> 前端首页「今日提醒」与该页共用此结果；不传 `petId` 时返回全部宠物。

#### 4.4.2 新建日程 `●`

`POST /schedule`

```json
{
  "petId": "mochi",
  "title": "体重复查",
  "type": "check",
  "date": "2026-10-20"
}
```

#### 4.4.3 更新日程 `●`

`PATCH /schedule/{id}`，可改 `title` / `date` / `type`。

#### 4.4.4 勾选完成 `●`

`PATCH /schedule/{id}/done`

```json
{ "done": true }
```

响应返回 `{ "id": "m1", "done": true }`。幂等：重复提交同值不报错。

#### 4.4.5 删除日程 `●`

`DELETE /schedule/{id}` → `204`。仅允许删除 `custom=true` 的自建条目，系统周期条目返回 `code=42201`。

#### 4.4.6 日程类型字典 `●`

`GET /schedule/types`

```json
{
  "data": {
    "vaccine": { "label": "疫苗", "icon": "calendar-check", "tone": "coral" },
    "deworm": { "label": "驱虫", "icon": "pill", "tone": "sage" },
    "check": { "label": "体检", "icon": "stethoscope", "tone": "sand" },
    "weight": { "label": "称重", "icon": "scale", "tone": "peach" },
    "groom": { "label": "洗护", "icon": "sparkle", "tone": "sage" },
    "feed": { "label": "喂食", "icon": "bowl", "tone": "peach" },
    "memo": { "label": "备忘", "icon": "note", "tone": "ink" },
    "other": { "label": "自定义", "icon": "calendar", "tone": "ink" }
  }
}
```

#### 4.4.7 备忘录 `●`

日程页内的随手记区，与日程条目**互相独立**（无日期、不参与到期计算），按置顶优先 + 创建时间倒序展示。

`GET /memo?petId=` → `{ "data": [{ "id": "mm1", "petId": "mochi", "text": "换粮要七天过渡", "pinned": true, "time": "2026-10-14 09:12" }] }`

`POST /memo`：`{ "petId": "mochi", "text": "周五带去打加强针" }`，text ≤200 字，服务端生成 `id`/`time`。

`PATCH /memo/{id}`：`{ "pinned": true }` 置顶/取消置顶（幂等）。

`DELETE /memo/{id}` → `204`。

#### 4.4.8 AI 一键生成日程计划 `●`

`POST /schedule/ai-plan`

按宠物档案（物种、年龄、疫苗/驱虫周期、下次到期日）生成一份**推荐计划**，前端展示为可勾选列表，用户确认后才真正写入（防止 AI 直接改用户数据）。

**请求体**：`{ "petId": "mochi" }`

**响应**

```json
{
  "data": {
    "planId": "sp_1001",
    "summary": "为「麻薯」生成 8 条计划：体外驱虫 7 天、体内驱虫 14 天、年度疫苗…",
    "items": [
      { "title": "体外驱虫", "type": "deworm", "date": "2026-10-21", "cycle": "每月一次", "note": "按福来恩/大宠爱交替使用" },
      { "title": "年度疫苗", "type": "vaccine", "date": "2026-11-02", "cycle": "每年一次", "note": "猫三联加强针" }
    ]
  }
}
```

**批量写入**：用户勾选确认后调 `POST /schedule/batch`，body 为 `{ "items": [ …同 items 结构，可带 petId ] }`。
服务端按 `title + petId` 去重：已存在的同名条目跳过并在响应 `skipped[]` 中返回，保证重复点击「一键添加」不会产生重复日程。

---

### 4.5 首页聚合

#### 4.5.1 首页数据 `●`

`GET /home?petId=mochi`

一次拉取首页所需全部数据，避免首屏多次请求：

```json
{
  "data": {
    "user": { "name": "林小满", "handle": "@manman", "initials": "满" },
    "pets": [ { "id": "mochi", "name": "麻薯" } ],
    "currentPetId": "mochi",
    "greeting": "下午好",
    "trend": [ { "day": "一", "value": 92, "label": "优" } ],
    "todayBoard": {
      "stats": { "overdue": 1, "today": 2, "done": 0 },
      "petFilter": "all",
      "pets": [ { "id": "mochi", "name": "麻薯", "pending": 3 }, { "id": "doudou", "name": "豆豆", "pending": 1 } ],
      "reminders": [
        {
          "id": "d5",
          "petId": "doudou",
          "petName": "豆豆",
          "species": "dog",
          "icon": "pill",
          "tone": "sage",
          "title": "体内外驱虫",
          "date": "2026-08-03",
          "diff": -72,
          "overdue": true,
          "dateText": "72 天前",
          "cycle": "每季度一次",
          "done": false
        }
      ],
      "remaining": 0
    },
    "reminders": [ { "icon": "calendar-check", "label": "年度疫苗", "date": "11-02", "state": "watch" } ],
    "announcements": [
      { "id": "a1", "title": "品种百科上线", "body": "...", "level": "event", "date": "2026-10-10" }
    ],
    "tips": [
      { "id": 1, "tag": "今日贴士", "title": "换季掉毛期", "body": "每日梳毛 5 分钟…", "tone": "sage" }
    ],
    "quickActions": [
      { "id": "scan", "label": "拍照识别", "sub": "品种 · 体态 · 状态", "icon": "camera", "route": "/recognize", "accent": true }
    ],
    "aiQuota": { "free": 3, "used": 0, "left": 3, "date": "2026-10-11" },
    "ongoingConsultCount": 1
  }
}
```

> `greeting` 由服务端按时区与 lingua 习惯生成（如「早上好」「下午好」），前端不再自行计算。

> `todayBoard` 是首页「今日提醒」大卡的数据源：聚合**当前用户名下全部宠物**的待办日程
> （`diff<=0` 且未完成，按日期升序，最多 4 条，超出进 `remaining`），`petFilter` 记录当前筛选
> （`all` 或宠物 id），`pets[].pending` 为各宠物待办数（筛选 chips 角标）。
> 旧字段 `reminders`（单宠物提醒）保留兼容，新客户端应改用 `todayBoard`。
> 完成动作走 `PATCH /schedule/{id}/done`（见 §4.4）。

---

### 4.6 公告与反馈

#### 4.6.1 生效公告 `●`

`GET /announcements?active=true`

```json
{
  "data": [
    {
      "id": "a1",
      "title": "品种百科上线",
      "body": "识别结果页新增「品种百科」入口…",
      "date": "2026-10-10",
      "level": "event",
      "active": true
    }
  ]
}
```

`level`：`event` 活动 / `warn` 警示 / `info` 通知。已被当前用户关闭的公告应被过滤。

#### 4.6.2 关闭公告 `●`

`POST /announcements/{id}/dismiss` → 记录用户维度已读，响应 `data: null`。

#### 4.6.3 提交意见反馈 `●`

`POST /feedbacks`

```json
{ "type": "bug", "text": "识别结果页偶尔白屏" }
```

`type`：`bug` 问题反馈 / `feature` 功能建议 / `other` 其他。
响应 `{ "id": "f1", "state": "open", "createdAt": "2026-10-11 23:00" }`。

---

### 4.7 拍照识别

> 识别能力对应项目中的 `cv/`（猫狗两个品种分类模型 + 物种路由）与 `services/vision` 在线推理。
> **模型只输出品种分类结果（top-k logits），不包含体态 / 健康分析**——页面上的品种档案、喂食建议均来自品种库查表（4.8），AI 建议来自问诊链路（4.10）。
> 若模型推理耗时较长，建议改为**异步模式**（见下方 4.7.4）。

#### 4.7.1 同步识别 `●`

`POST /recognitions` — `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `image` | file | 是 | 图片，≤10MB，jpg/png/webp |
| `petId` | string | 否 | 关联宠物，写入识别历史 |
| `species` | string | 否 | `auto`（默认，路由到狗/猫模型取最高置信）/ `dog` / `cat` |

**响应**

```json
{
  "data": {
    "id": "rc1770000000000",
    "title": "英国短毛猫",
    "sci": "Felis catus",
    "confidence": 0.96,
    "species": "cat",
    "breedId": "b-bsh",
    "risk": "confirmed",
    "alternatives": [
      { "title": "英国短毛猫", "confidence": 0.96 },
      { "title": "苏格兰折耳猫", "confidence": 0.02 },
      { "title": "中华田园猫", "confidence": 0.01 }
    ],
    "breedProfile": {
      "origin": "英国",
      "temperament": ["温和沉静", "独立不强求", "对陌生人有分寸"],
      "weight": "4 – 7.5 kg",
      "life": "12 – 15 年",
      "feeding": ["以优质动物蛋白为主（鸡肉、鱼肉、牛肉），低碳水防止发胖", "…"]
    }
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `risk` | 置信度分级：`confirmed` ≥0.85 / `uncertain` 0.45–0.85 / `rejected` <0.45（拒识，此时 `title` 为空、仅返回 alternatives） |
| `alternatives` | 模型 top-3，供用户「识别不准」时参考与手动纠正 |
| `breedProfile` | top1 品种档案摘要（来自品种库查表，**非模型推理**）；品种库未收录时为 `null` |

> 手动纠正提交后，本条识别记录的 `corrected` / `status` 才会变化（见 4.7.3）。

#### 4.7.2 识别历史 `●`

`GET /recognitions?page=1&pageSize=20`

```json
{
  "data": {
    "list": [
      {
        "id": "rc1770000000000",
        "species": "cat",
        "predicted": "英国短毛猫",
        "corrected": null,
        "confidence": 0.96,
        "alternatives": [],
        "status": "done",
        "imageRef": "demo",
        "time": "2026-10-14T10:52:00.000Z"
      }
    ],
    "total": 12
  }
}
```

`status`：`done` 识别完成（未纠正） / `review` 已手动纠正待审核 / `approved` 审核通过（计入训练数据集） / `rejected` 审核驳回（维持模型原预测）。

#### 4.7.3 提交手动纠正 `●`

`POST /recognitions/{id}/correction`

```json
{ "breed": "苏格兰折耳猫" }
```

**行为**：`breed` 必须是品种库中与 `species` 一致的品种名；记录进入管理端审核队列（`status → review`）。用户侧立即按纠正后的品种展示，审核通过前标注「纠正待审核」。

**响应**：更新后的识别记录对象（同 4.7.2 列表项）。

#### 4.7.4 异步识别（推理较慢时推荐）

`POST /recognitions/async` → `{ "taskId": "t1" }`
`GET /recognitions/tasks/{taskId}` → `{ "state": "pending|success|failed", "result": {...} }`

建议配合 WebSocket 主动推送结果，避免前端轮询。

---

### 4.8 品种百科

#### 4.8.1 品种列表 `○`

`GET /breeds?species=cat&keyword=英短`

```json
{
  "data": [
    { "id": "b-bsh", "name": "英国短毛猫", "sci": "Felis catus", "species": "cat", "origin": "英国" }
  ]
}
```

#### 4.8.2 品种详情 `●`

`GET /breeds/{id}`

```json
{
  "data": {
    "id": "b-bsh",
    "name": "英国短毛猫",
    "sci": "Felis catus",
    "species": "cat",
    "origin": "英国",
    "temperament": ["温和沉静", "独立不强求", "对陌生人有分寸"],
    "weight": "4 – 7.5 kg",
    "life": "12 – 15 年",
    "issues": ["肥厚型心肌病", "肥胖倾向", "多囊肾（少见）"],
    "care": "被毛短而致密，每周梳理 1–2 次即可…",
    "feeding": [
      "以优质动物蛋白为主（鸡肉、鱼肉、牛肉），低碳水防止发胖",
      "成猫每日 60–80 g，分 2–3 餐投喂，固定品牌减少软便",
      "零食不超过每日总热量 10%，不喂人食（洋葱/巧克力致命）",
      "用饮水机或湿粮拌水骗水，预防泌尿问题"
    ],
    "aiPrompts": ["英短特别容易发胖，怎么科学控制体重？", "英短幼猫一天喂几顿、喂多少合适？"],
    "coverUrl": null
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `feeding` | 喂食建议（编号列表，识别结果页取前 2 条展示） |
| `aiPrompts` | 联动 AI 问诊的快捷提问：点击后以 `{ pet: <品种名>, note: <问题原文> }` 进入 `/consult/ai`，由知识库检索补充该品种语料后作答 |
| `issues` / `care` | 易患问题 / 护理要点（原有字段） |

> 品种档案是「识别 → 建议」的查表数据源：所有建议内容均来自本接口与知识库，**不经过视觉模型推理**。

---

### 4.9 问诊：元信息与词典

#### 4.9.1 科室列表 `○`

`GET /consult/departments`

```json
{
  "data": [
    { "id": "all", "label": "全部", "icon": "stethoscope" },
    { "id": "internal", "label": "犬猫内科", "icon": "heart" },
    { "id": "surgery", "label": "外科骨科", "icon": "firstaid" },
    { "id": "derma", "label": "皮肤病", "icon": "sparkle" },
    { "id": "er", "label": "急诊重症", "icon": "alert" },
    { "id": "exotic", "label": "异宠专科", "icon": "paw" },
    { "id": "nutrition", "label": "营养体重", "icon": "scale" },
    { "id": "eye", "label": "眼科", "icon": "eye" }
  ]
}
```

#### 4.9.2 问诊方式 `○`

`GET /consult/modes`

```json
{
  "data": [
    {
      "id": "text",
      "label": "图文问诊",
      "icon": "comment",
      "price": 19,
      "desc": "上传照片与描述，医生 24h 内回复，可追问 3 次",
      "eta": "平均 8 分钟接诊"
    },
    { "id": "voice", "label": "电话问诊", "icon": "phone", "price": 39, "desc": "...", "eta": "15 分钟通话" },
    { "id": "video", "label": "视频问诊", "icon": "video", "price": 59, "desc": "...", "eta": "20 分钟通话" }
  ]
}
```

> 价格由服务端下发，前端不硬编码，便于运营调价。

#### 4.9.3 结构化问诊词典 `○`

`GET /consult/dictionary`

一次性返回向导式预问诊所需的全部选项（前端 7 步向导依赖），也便于运营后台维护：

```json
{
  "data": {
    "bodyParts": [
      {
        "id": "digest",
        "label": "消化系统",
        "icon": "heart",
        "symptoms": [
          { "id": "vomit", "label": "呕吐" },
          { "id": "blood-stool", "label": "便中带血", "redFlag": false, "weight": 2 },
          { "id": "appetite", "label": "食欲下降 / 拒食" }
        ]
      },
      {
        "id": "breath",
        "label": "呼吸循环",
        "icon": "heart",
        "symptoms": [
          { "id": "breath-open", "label": "张嘴呼吸 / 喘不上气", "redFlag": true },
          { "id": "pale", "label": "舌色发白或发紫", "redFlag": true }
        ]
      }
    ],
    "durations": [
      { "id": "today", "label": "今天刚开始", "w": 0 },
      { "id": "2-3d", "label": "2–3 天", "w": 1 },
      { "id": "1w", "label": "约一周", "w": 2 },
      { "id": "1w+", "label": "超过一周", "w": 3 }
    ],
    "severities": [
      { "id": "mild", "label": "轻微 · 吃喝玩正常", "w": 0 },
      { "id": "mid", "label": "明显不适 · 但能进食", "w": 2 },
      { "id": "severe", "label": "精神差 · 不吃不喝", "w": 4 }
    ],
    "accompanyOptions": [
      { "id": "spirit", "label": "精神萎靡", "w": 3 },
      { "id": "fever", "label": "身体发热 / 耳朵发烫", "w": 2 }
    ],
    "symptomGroups": [
      { "group": "消化", "items": ["呕吐", "软便腹泻", "食欲下降", "便秘"] }
    ]
  }
}
```

字段约定：

- `redFlag: true` —— **高危信号**，分诊引擎需一票否决判为急症。
- `w` / `weight` —— 分诊加权分值，详见 [4.10](#410-问诊ai-分诊与额度)。

---

### 4.10 问诊：AI 分诊与额度

#### 4.10.1 查询 AI 免费额度 `●`

`GET /consult/ai-quota`

```json
{ "data": { "date": "2026-10-11", "free": 3, "used": 1, "left": 2 } }
```

> 跨自然日自动重置。**额度判定与扣减必须由服务端完成**，前端仅做展示与引导。

#### 4.10.2 AI 自由文本分诊 `●`

`POST /consult/triage`

用于 AI 智能问诊页的自然语言输入（对应前端 `/consult/ai`）。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `text` | string | 是 | 用户描述的症状，≤500 字 |
| `petId` | string | 否 | 携带宠物档案上下文（品种/年龄/体重） |
| `images` | array | 否 | 已上传图片 URL 数组 |
| `sessionId` | string | 否 | 多轮追问上下文 ID |
| `contextRecords` | array | 否 | 用户从健康档案勾选导入的记录（见下方「档案导入」） |
| `rag` | bool | 否 | 是否启用品种知识库检索（默认 true） |

**响应**

```json
{
  "data": {
    "sessionId": "cs_1001",
    "triage": {
      "level": "urgent",
      "score": 4,
      "label": "建议尽快就诊",
      "short": "24 小时内预约医生",
      "advice": "症状需要专业检查才能确诊。建议 24 小时内完成一次面诊或线上问诊，不要自行用药。",
      "causes": ["毛球症", "胃肠炎", "异物梗阻"],
      "actions": [
        "记录症状开始时间与频次",
        "拍摄清晰照片或视频备用",
        "暂停自行给药，避免掩盖症状"
      ],
      "followUp": "建议 24 小时内完成一次线上或线下面诊；用药 3 天无改善需复诊。",
      "factors": [
        { "text": "已持续「2–3 天」", "w": 1 },
        { "text": "伴随「精神萎靡」", "w": 3 }
      ],
      "dept": "internal",
      "cite": "英国短毛猫品种档案 · 易患问题：心肌病、多囊肾",
      "citeBreedId": "british-shorthair"
    },
    "reply": "根据描述，呕吐持续 2–3 天且精神偏弱，建议尽快做一次面诊…",
    "quota": { "free": 3, "used": 2, "left": 1 }
  }
}
```

**RAG 品种知识引用（`rag=true` 时）**

服务端按 `petId` 对应的品种检索品种库（`breed` 表），把「易患疾病 / 护理要点」注入 `system prompt`，并在分诊卡上返回引用字段，前端渲染为「参考知识库」行 + 品种档案链接：

| 字段 | 说明 |
| --- | --- |
| `cite` | 引用摘要，如「英国短毛猫品种档案 · 易患问题：心肌病、多囊肾」 |
| `citeBreedId` | 被引用品种 ID，前端跳 `/breed/{id}` |

> 检索为空（品种库未收录）时两个字段省略，前端不渲染引用行；**不得编造引用**。

**档案导入（`contextRecords`）**

前端「从档案导入近期变化」把用户勾选的健康记录 / 识别记录 / 历史报告打包随消息提交，服务端将其作为会话上下文（渲染为 context 卡片，不计入用户输入字数）：

```json
"contextRecords": [
  { "kind": "record", "label": "体重", "value": "4.6 kg", "date": "2026-10-10", "note": "较上周 +0.2" },
  { "kind": "recognition", "label": "品种识别", "value": "英国短毛猫", "date": "2026-10-12", "note": "置信度 96%" }
]
```

`level` 三级枚举：

| level | 含义 | 前端表现 |
| --- | --- | --- |
| `emergency` | 疑似急症 | 红色告警条 + 强制提示线下急诊按钮 |
| `urgent` | 建议就诊 | 橙色标签 + 推荐转真人医生 |
| `home` | 居家观察 | 苔绿标签 + 护理建议 |

`factors[]` 为**可解释评分依据**（`w` 为该加分项分值，`danger:true` 表示高危一票否决项），
报告页会直接展示给用户，**后端务必返回**，不可省略。

#### 4.10.3 结构化预问诊提交 `●`

`POST /consult/pre-consult`

7 步向导收集完毕后一次提交，**服务端返回分诊结论并同时生成报告**。

**请求体**

```json
{
  "petId": "mochi",
  "partId": "digest",
  "symptomIds": ["vomit", "appetite"],
  "durationId": "2-3d",
  "severityId": "mid",
  "accompanyIds": ["spirit"],
  "note": "昨天吐了两次，都是未消化的猫粮",
  "photoCount": 2,
  "saveReport": true
}
```

**响应**

```json
{
  "data": {
    "triage": { "level": "urgent", "score": 6, "factors": [] },
    "reportId": "rp1760000000000"
  }
}
```

> 若 `saveReport=false`，仅返回 `triage` 不落报告。

#### 4.10.4 分诊引擎实现约定（后端注意）

前端已有一份规则实现（`apps/mobile/src/data/triage.js`），后端可直接移植或替换为模型，**但输出结构必须与之一致**：

```text
1) 存在任意 redFlag 症状 → level=emergency, score=10, factors 含 { danger: true } 项，立即短路返回
2) 否则 score = duration.w + severity.w + Σsymptom.weight + Σaccompany.w
3) score >= 3 → urgent；否则 home
4) causes 由症状 → 病因知识库映射去重后取前 5 条
5) actions 依据 level 的基础模板 + 按 partId 追加（如 skin → 每日同角度拍照对比）
```

推荐形态：**大模型输出 + 规则兜底**。模型不可用时退化为上述规则引擎，保证服务可用性。

#### 4.10.5 AI 病例摘要（转真人时用）`●`

`POST /consult/case-summary`

转诊时生成结构化摘要递给医生，避免重复追问（这是本模块的核心设计点）。

```json
{
  "petId": "mochi",
  "symptomLabels": ["呕吐", "食欲下降"],
  "durationLabel": "2–3 天",
  "severityLabel": "明显不适 · 但能进食",
  "accompanyLabels": ["精神萎靡"],
  "triage": { "level": "urgent", "label": "建议尽快就诊" },
  "note": "昨天吐了两次"
}
```

**响应**

```json
{
  "data": {
    "summary": {
      "pet": { "id": "mochi", "name": "麻薯", "breed": "英国短毛猫", "age": 3, "weight": 4.6 },
      "symptoms": ["呕吐", "食欲下降"],
      "duration": "2–3 天",
      "severity": "明显不适 · 但能进食",
      "complaints": ["精神萎靡"],
      "aiTriage": { "level": "urgent", "label": "建议尽快就诊" },
      "note": "昨天吐了两次",
      "text": "3 岁英短母猫，体重 4.6kg。近 2–3 天出现呕吐、食欲下降，精神偏弱。AI 初判：建议尽快就诊。"
    }
  }
}
```

---

### 4.11 问诊：医生

#### 4.11.1 医生列表 `○`

`GET /doctors?dept=internal&online=true&sort=rating&page=1&pageSize=20`

| 参数 | 说明 |
| --- | --- |
| `dept` | 科室 id，`all` 或不传为全部 |
| `online` | `true` 仅在线 |
| `sort` | `default` 在线优先 / `rating` 评分 / `consults` 接诊量 / `response` 响应速度 |

```json
{
  "data": {
    "list": [
      {
        "id": "d1",
        "name": "陈静",
        "title": "主治医师",
        "dept": "internal",
        "deptLabel": "犬猫内科",
        "hospital": "Petwise 合作动物医院 · 城西院区",
        "years": 9,
        "rating": 4.9,
        "consults": 3240,
        "online": true,
        "responseMin": 6,
        "tags": ["猫科消化", "呼吸道", "慢病管理"],
        "slot": "今日 14:00–22:00 可约",
        "avatarUrl": null
      }
    ],
    "total": 7,
    "onlineCount": 5,
    "page": 1,
    "pageSize": 20,
    "hasMore": false
  }
}
```

#### 4.11.2 医生详情 `○`

`GET /doctors/{id}`

```json
{
  "data": {
    "id": "d1",
    "name": "陈静",
    "title": "主治医师",
    "deptLabel": "犬猫内科",
    "hospital": "Petwise 合作动物医院 · 城西院区",
    "years": 9,
    "rating": 4.9,
    "consults": 3240,
    "online": true,
    "responseMin": 6,
    "tags": ["猫科消化", "呼吸道", "慢病管理"],
    "good": ["猫传腹", "慢性呕吐", "软便腹泻"],
    "intro": "专注猫科内科九年…",
    "certs": ["执业兽医师资格证", "中国畜牧兽医学会会员"],
    "slot": "今日 14:00–22:00 可约",
    "reviews": [
      { "id": "rv1", "user": "橘座本座", "rating": 5, "text": "猫呕吐三天，医生问得很细…", "time": "2 天前" }
    ]
  }
}
```

#### 4.11.3 医生评价列表 `○`

`GET /doctors/{id}/reviews?page=1&pageSize=20`

---

### 4.12 问诊：问诊单与实时消息

#### 4.12.1 创建问诊单（下单）`●`

`POST /consult/orders`

请求头建议带 `Idempotency-Key`，防止重复下单。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `doctorId` | string | 是 | 医生 ID |
| `mode` | string | 是 | `text` / `voice` / `video` |
| `petId` | string | 是 | 问诊宠物 |
| `summary` | object | 否 | AI 病例摘要（见 4.10.5），可由用户编辑 |
| `price` | number | 是 | 服务端应校验与医生×方式价格一致，不一致返回 `code=10002` |

**响应**（`201`）

```json
{
  "data": {
    "id": "o1760000000000",
    "doctorId": "d2",
    "mode": "video",
    "petId": "mochi",
    "summary": { "symptoms": ["呕吐"], "text": "…" },
    "price": 59,
    "state": "pending",
    "createdAt": "2026-10-11T23:00:00+08:00",
    "messages": []
  }
}
```

`state` 流转：`pending` 待接诊 → `replied` 医生已回复 → `closed` 已结束。

#### 4.12.2 问诊单列表 `●`

`GET /consult/orders?state=ongoing`

`state` 传 `ongoing` 返回未结束的（`pending` + `replied`），用于首页/中心页「进行中的问诊」。

```json
{
  "data": [
    {
      "id": "o1760000000000",
      "doctorId": "d2",
      "mode": "video",
      "petId": "mochi",
      "state": "pending",
      "createdAt": "2026-10-11T23:00:00+08:00",
      "doctor": { "id": "d2", "name": "王铮", "deptLabel": "急诊重症" },
      "pet": { "id": "mochi", "name": "麻薯" },
      "lastMessage": { "type": "system", "text": "医生正在查看你的病例摘要…" },
      "unread": 0
    }
  ]
}
```

#### 4.12.3 问诊单详情 `●`

`GET /consult/orders/{id}` —— 返回完整对象，含 `messages` 数组。

#### 4.12.4 拉取消息 `●`

`GET /consult/orders/{id}/messages?beforeId=&limit=50`

```json
{
  "data": {
    "list": [
      { "id": "m1", "type": "user", "text": "医生你好，它昨晚吐了一次", "createdAt": "2026-10-11T23:01:00+08:00" },
      { "id": "m2", "type": "system", "text": "王铮医生已接诊", "createdAt": "2026-10-11T23:02:00+08:00" },
      {
        "id": "m3",
        "type": "rx",
        "text": "处方已开具",
        "drugs": [
          { "name": "硫糖铝片", "dose": "每次 250mg", "usage": "每日 2 次，连用 3 天", "days": 3 }
        ],
        "note": "饭后半小时服用，如出现呕吐加重立即停药并复诊。",
        "createdAt": "2026-10-11T23:05:00+08:00"
      }
    ],
    "hasMore": false
  }
}
```

`type`：`user` / `doctor` / `system` / `rx`（处方卡，前端渲染为卡片而非普通气泡）。

#### 4.12.5 发送消息 `●`

`POST /consult/orders/{id}/messages`

```json
{ "text": "医生你好，它昨晚吐了一次", "images": ["https://.../a.jpg"] }
```

响应返回持久化后的消息对象，并通过 WebSocket 推送给医生。

约束：`state=closed` 的订单不可发送，返回 `code=42001`。

#### 4.12.6 发起通话 `●`

`POST /consult/orders/{id}/call`

仅 `voice` / `video` 方式可用。返回通话凭证：

```json
{ "data": { "channel": "pw_o1760000000000", "token": "rtc_xxx", "expiresIn": 3600 } }
```

前端接入第三方实时音视频 SDK（声网/腾讯 TRTC）时使用。

#### 4.12.7 结束问诊 `●`

`POST /consult/orders/{id}/close`

订单置为 `closed`，返回更新后的订单。**结束后由服务端自动生成真人问诊报告**（见 4.13.4），响应携带 `reportId`。

#### 4.12.8 标记消息已读 `●`

`POST /consult/orders/{id}/read`，请求 `{ "lastMessageId": "m3" }`。

---

### 4.13 问诊：评价与报告

#### 4.13.1 提交评价 `●`

`POST /consult/orders/{id}/rating`

```json
{ "score": 5, "tags": ["回复及时", "解释清楚", "方案有效"] }
```

`score` 1–5 星。同一订单重复提交为更新操作。响应：

```json
{ "data": { "orderId": "o1", "doctorId": "d2", "score": 5, "tags": ["回复及时"] } }
```

#### 4.13.2 我的评价 `●`

`GET /consult/ratings?orderId=`

#### 4.13.3 问诊报告列表 `●`

`GET /consult/reports?type=&petId=&page=1&pageSize=20`

```json
{
  "data": {
    "list": [
      {
        "id": "rp1760000000000",
        "type": "ai",
        "petId": "mochi",
        "petName": "麻薯",
        "title": "麻薯 · 呕吐",
        "preview": "建议尽快就诊 — 24 小时内预约医生",
        "date": "2026-10-11",
        "archived": false,
        "reminded": false,
        "triage": { "level": "urgent", "label": "建议尽快就诊", "short": "24 小时内预约医生" }
      }
    ],
    "total": 7
  }
}
```

#### 4.13.4 创建/保存报告 `●`

`POST /consult/reports`

AI 预问诊完成或真人问诊结束时调用。**请求结构必须与前端现有报告对象一致**：

```json
{
  "type": "ai",
  "petId": "mochi",
  "petName": "麻薯",
  "orderId": null,
  "title": "麻薯 · 呕吐",
  "preview": "建议尽快就诊 — 24 小时内预约医生",
  "chief": {
    "partLabel": "消化系统",
    "symptomLabels": ["呕吐", "食欲下降"],
    "durationLabel": "2–3 天",
    "severityLabel": "明显不适 · 但能进食",
    "accompanyLabels": ["精神萎靡"],
    "note": "昨天吐了两次",
    "photos": 0
  },
  "triage": {
    "level": "urgent",
    "label": "建议尽快就诊",
    "short": "24 小时内预约医生",
    "advice": "症状需要专业检查才能确诊…",
    "causes": ["毛球症", "胃肠炎"],
    "actions": ["记录症状开始时间与频次"],
    "score": 6,
    "factors": [{ "text": "已持续「2–3 天」", "w": 1 }],
    "followUp": "建议 24 小时内完成一次线上或线下面诊"
  },
  "doctor": null,
  "doctorAdvice": null,
  "rx": null
}
```

真人问诊结束时（`type=human`）额外携带：

```json
{
  "type": "human",
  "orderId": "o1760000000000",
  "doctor": { "id": "d2", "name": "王铮", "title": "主任医师" },
  "doctorAdvice": "先禁食 4 小时观察，之后少量多次喂水…",
  "rx": {
    "drugs": [{ "name": "硫糖铝片", "dose": "每次 250mg", "usage": "每日 2 次，连用 3 天", "days": 3 }],
    "note": "饭后半小时服用"
  }
}
```

响应返回带 `id` / `createdAt` / `date` / `archived` / `reminded` 的完整报告。

#### 4.13.5 报告详情 `●`

`GET /consult/reports/{id}` —— 返回完整报告对象。

#### 4.13.6 报告回流健康档案 `●`

`POST /consult/reports/{id}/archive`

服务端写入一条 `kind=symptom` 的健康记录：

```text
【问诊报告】呕吐、食欲下降 — 建议尽快就诊。症状需要专业检查才能确诊…
```

响应 `{ "data": { "archived": true, "recordId": "r100" } }`。
**幂等**：已归档重复调用返回 `archived: true` 且不新增记录（`code=0`）。

#### 4.13.7 报告转日程提醒 `●`

`POST /consult/reports/{id}/remind`

服务端按报告内容生成日程：

| 生成项 | 规则 |
| --- | --- |
| 用药提醒 | 存在 `rx.drugs` 时，`type=other`，标题「按处方用药：xxx」，`date = 报告日期 + 1 天` |
| 复查提醒 | 必定生成，`type=check`；`level=home` 时标题「复查：症状是否缓解」且 `+3 天`，否则「复诊：按医生建议回访」且 `+7 天` |

```json
{ "data": { "reminded": true, "items": [{ "id": "s1", "title": "按处方用药：硫糖铝片", "date": "2026-10-12" }] } }
```

同样需幂等。`reminded` 为 `true` 时重复调用直接返回已生成条目，不重复写。

#### 4.13.8 导出报告 `●`

`GET /consult/reports/{id}/export?format=pdf`

返回 PDF 文件流（`application/pdf`）。建议同时提供 `format=png` 长图以便分享。

---

### 4.14 社区

#### 4.14.1 动态列表 `●`

`GET /posts?page=1&pageSize=20&tag=`

```json
{
  "data": {
    "list": [
      {
        "id": "p1",
        "author": "阿橘的日常",
        "authorId": "u2",
        "role": null,
        "avatarUrl": null,
        "time": "12 分钟前",
        "text": "麻薯今天第一次主动跳上猫爬架顶端…",
        "images": ["https://.../1.jpg", "https://.../2.jpg"],
        "tags": ["#成长记录", "#英短"],
        "likes": 128,
        "comments": 23,
        "liked": false
      }
    ],
    "total": 86,
    "page": 1,
    "pageSize": 20,
    "hasMore": true
  }
}
```

> `time` 建议由服务端返回相对时间文本，避免各端时区/文案不一致；也可返回 `createdAt` 由前端格式化。

#### 4.14.2 发布动态 `●`

`POST /posts`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `text` | string | 是 | 正文，≤1000 字 |
| `images` | array | 否 | 已上传图片 URL，≤9 张 |
| `tags` | array | 否 | 话题标签，如 `["#成长记录"]` |

返回完整帖子对象，`201`。

#### 4.14.3 帖子详情 `●`

`GET /posts/{id}`

#### 4.14.4 点赞 / 取消点赞 `●`

`POST /posts/{id}/like` · `DELETE /posts/{id}/like`

```json
{ "data": { "liked": true, "likes": 129 } }
```

#### 4.14.5 评论列表 `●`

`GET /posts/{id}/comments?page=1&pageSize=20`

```json
{
  "data": {
    "list": [
      { "id": "cm1", "userId": "u3", "name": "豆豆妈", "text": "太治愈了！", "time": "8分钟前", "liked": false }
    ],
    "total": 3
  }
}
```

#### 4.14.6 发表评论 `●`

`POST /posts/{id}/comments`，请求 `{ "text": "..." }`。

#### 4.14.7 举报帖子 `●`

`POST /posts/{id}/report`

社区「更多 → 举报」入口，写入后进入管理端「内容审核 → 举报处理」队列。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `reason` | string | 是 | 举报理由枚举：`广告或垃圾信息` / `辱骂攻击` / `血腥暴力` / `违法违规` / `侵犯权益` / `其他` |
| `detail` | string | 否 | 补充说明，≤200 字 |

```json
{ "data": { "id": "rp1760000000000", "state": "pending" } }
```

> 同一用户对同一帖子的重复举报返回 `code=42202`（前端提示「你已举报过这条动态」）。
> 举报记录结构见 §3 数据模型 `post_report`；管理端处理接口见 4.18.8。

---

### 4.15 即时消息 IM

> IM 与问诊消息是两套独立通道：问诊消息绑定问诊单，IM 为社交会话。

#### 4.15.1 会话列表 `●`

`GET /conversations`

```json
{
  "data": [
    {
      "id": "c1",
      "name": "兽医老张",
      "avatarUrl": null,
      "last": "麻薯的便便状态拍给我看看～",
      "time": "09:30",
      "unread": 2,
      "online": true,
      "kind": "vet"
    }
  ]
}
```

`kind`：`vet` 兽医 / `group` 群聊 / `friend` 好友。

#### 4.15.2 会话消息 `●`

`GET /conversations/{id}/messages?beforeId=&limit=50`

```json
{
  "data": {
    "list": [
      { "id": "m1", "role": "them", "text": "你好，麻薯最近状态怎么样？", "time": "09:12" },
      { "id": "m2", "role": "me", "text": "昨天开始有点软便", "time": "09:14" }
    ],
    "hasMore": false
  }
}
```

#### 4.15.3 发送消息 `●`

`POST /conversations/{id}/messages`，请求同 4.12.5。

#### 4.15.4 标记已读 `●`

`POST /conversations/{id}/read` → `{ "data": { "unread": 0 } }`

#### 4.15.5 通讯录 `●`

`GET /contacts?q=`

```json
{
  "data": {
    "groups": [
      {
        "id": "friends",
        "label": "我的好友",
        "members": [
          {
            "id": "ct-aju",
            "name": "阿橘的日常",
            "kind": "friend",
            "bio": "英短麻薯的家长 · 换季护理达人",
            "online": false,
            "chatId": null,
            "doctorId": null,
            "pet": { "name": "麻薯", "breed": "英国短毛猫", "age": 1 },
            "posts": 9,
            "fans": "1.2k"
          }
        ]
      },
      { "id": "vets", "label": "我的兽医", "members": [] },
      { "id": "groups", "label": "宠物社群", "members": [] }
    ],
    "total": 10
  }
}
```

**字段约定**

| 字段 | 说明 |
| --- | --- |
| `kind` | `vet` 执业兽医 / `group` 群聊 / `friend` 好友 |
| `chatId` | 非空 → 客户端直达 `GET /conversations/{chatId}/messages` |
| `doctorId` | 非空 → 客户端跳兽医资料页 `GET /doctors/{doctorId}` |
| 两者皆空 | 客户端以联系人 id 发起新会话：`POST /conversations`（body `{ "contactId": "ct-aju" }`）返回会话 id |

`q` 为可选关键字，按姓名/简介过滤；命中为空的分组不返回。

#### 4.15.6 发起会话 `●`

`POST /conversations`，请求 `{ "contactId": "ct-aju" }`，返回新建（或已存在）的会话对象，结构同 4.15.1 单项。

---

### 4.16 收藏

#### 4.16.1 收藏列表 `●`

`GET /favorites?kind=`

```json
{
  "data": [
    { "id": "f1", "kind": "breed", "title": "英国短毛猫", "desc": "温和沉静 · 寿命 12–15 年", "route": "/breed/b-bsh" },
    { "id": "f3", "kind": "post", "title": "麻薯第一次跳上猫爬架顶端", "desc": "阿橘的日常 · 128 赞", "route": "/community" }
  ]
}
```

`kind`：`breed` 品种 / `post` 帖子 / `tip` 贴士。

#### 4.16.2 添加收藏 `●`

`POST /favorites`，请求 `{ "kind": "breed", "targetId": "b-bsh" }`。

#### 4.16.3 取消收藏 `●`

`DELETE /favorites/{kind}/{targetId}` → `204`

---

### 4.17 文件上传

#### 4.17.1 通用上传 `●`

`POST /files` — `multipart/form-data`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `file` | file | 单文件，图片 ≤10MB，视频 ≤100MB |
| `scene` | string | `avatar` / `post` / `recognition` / `consult` |

```json
{
  "data": {
    "url": "https://cdn.example.com/petwise/2026/10/11/abc123.jpg",
    "key": "petwise/2026/10/11/abc123.jpg",
    "size": 204800,
    "mimeType": "image/jpeg",
    "width": 1080,
    "height": 1440
  }
}
```

约束：按 `scene` 校验 MIME 白名单；图片需服务端压缩/裁图；建议返回 CDN 直传签名供大文件直传。

---

### 4.18 管理端

> 管理端统一走 `/admin/**`，需 `role=admin` 令牌，否则返回 `code=20004`。

#### 4.18.1 数据概览 `●`

`GET /admin/overview`

```json
{
  "data": {
    "userCount": 1286,
    "petCount": 2043,
    "orderCount": 356,
    "todayOrders": 12,
    "pendingFeedbacks": 4,
    "activeAnnouncements": 2,
    "aiUsageToday": 189,
    "revenueToday": 2277.00
  }
}
```

#### 4.18.2 公告管理 `●`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/announcements?page=&pageSize=` | 列表（含未启用） |
| POST | `/admin/announcements` | 新建 `{title, body, level, active}` |
| PATCH | `/admin/announcements/{id}` | 编辑/启停 |
| DELETE | `/admin/announcements/{id}` | 删除 |

```json
{
  "id": "a1",
  "title": "品种百科上线",
  "body": "识别结果页新增「品种百科」入口…",
  "level": "event",
  "active": true,
  "date": "2026-10-10"
}
```

#### 4.18.3 反馈处理 `●`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/feedbacks?state=&page=` | 列表 |
| PATCH | `/admin/feedbacks/{id}` | 处理 `{state, reply}` |

```json
{
  "id": "f1",
  "userId": "u1",
  "user": "138****1111",
  "type": "bug",
  "text": "识别结果页偶尔白屏",
  "state": "open",
  "reply": null,
  "time": "2026-10-11 23:00"
}
```

`state`：`open` 待处理 / `processing` 处理中 / `resolved` 已解决。

#### 4.18.4 字典维护 `●`

词典（4.9.3 的 `bodyParts` / `symptomIds` 等）建议由后台维护，提供：

| 方法 | 路径 |
| --- | --- |
| GET | `/admin/dictionary` |
| PUT | `/admin/dictionary` （全量覆盖） |
| POST | `/admin/dictionary/symptoms` （新增症状） |
| PATCH | `/admin/dictionary/symptoms/{id}` |

#### 4.18.5 识别记录审核 `●`

管理端对用户手动纠正的识别记录进行审核，实现「用户纠正 → 审核 → 数据回流」闭环。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/recognitions?state=&page=` | 识别记录列表；`state`：`done / review / approved / rejected / failed`，支持 `keyword` 搜索用户/品种 |
| POST | `/admin/recognitions/{id}/review` | 审核 `{ pass: true }` 通过（`status → approved`，计入训练数据集）；`{ pass: false }` 驳回（`status → rejected`，展示回模型原预测，`corrected` 清空） |

**列表项结构**（与 4.7.2 列表项一致，附管理端展示字段）：

```json
{
  "id": "rc-demo1",
  "user": "柯基豆豆妈",
  "pet": "豆豆",
  "species": "dog",
  "predicted": "柯基犬",
  "corrected": "瑞典柯基犬",
  "confidence": 0.61,
  "time": "2026-10-14 16:40",
  "status": "review"
}
```

> 置信度 <0.60 的记录由系统自动标记 `review`（低置信待审），与用户手动纠正的 `review` 在列表中以「低置信待审 / 纠正待审核」区分。

#### 4.18.6 导出训练数据集 `●`

`POST /admin/recognitions/dataset/export`

将全部 `status=approved` 的纠正样本导出为训练数据集（增量训练用）。

**响应**（或直接返回文件下载，`Content-Disposition: attachment`）：

```json
{
  "data": {
    "dataset": "petwise-corrections",
    "count": 1,
    "samples": [
      {
        "image_ref": "rc-demo3",
        "species": "cat",
        "label": "苏格兰折耳猫",
        "model_predicted": "英国短毛猫",
        "model_confidence": 0.79,
        "source": "user_correction",
        "reviewed": true
      }
    ]
  }
}
```

**落地约定**：导出的 `image_ref` 需能在对象存储中取到原图（识别时持久化的图片 key）；`label` 为人工确认标签，可直接拼入 `cv/dog` 或 `cv/cat` 的 `ImageFolder` 结构做增量训练（见 `cv/README.md`）。建议按周导出，导出后服务端将这批样本标记 `exported`，避免重复导出。

#### 4.18.7 用户与兽医管理 `●`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/users?state=&keyword=&page=` | C 端用户列表；`state`：`active` / `frozen` |
| POST | `/admin/users` | 新增用户 `{ name, phone, password, petCount? }`；手机号重复 `code=42204` |
| PATCH | `/admin/users/{id}` | 改状态 `{ state: 'frozen' \| 'active' }` 冻结/恢复 |
| DELETE | `/admin/users/{id}` | 删除（演示内置账号不可删） |
| POST | `/admin/users/{id}/password-reset` | 重置密码，返回一次性新密码 `{ password: "430090" }`（管理员抄送用户） |
| GET | `/admin/doctors?dept=&online=` | 兽医账号列表 |
| POST | `/admin/doctors` | 新增兽医 `{ name, dept, hospital, phone, online }` |
| PATCH | `/admin/doctors/{id}` | 改科室/医院/上下线/冻结 |
| DELETE | `/admin/doctors/{id}` | 删除兽医账号 |

> 兽医账号与 C 端用户是两套身份：兽医可登录医生工作台接诊，`state='frozen'` 时强制下线。

#### 4.18.8 内容审核与举报处理 `●`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/posts?state=&page=` | 社区内容列表；`state`：`pending / pass / reject` |
| POST | `/admin/posts/{id}/review` | 人工审核 `{ pass: true }` 通过 / `{ pass: false }` 驳回（下架并通知作者） |
| GET | `/admin/post-reports?state=&page=` | 举报队列；`state`：`pending / removed / ignored` |
| POST | `/admin/post-reports/{id}/handle` | 处理举报 `{ action: 'remove' }` 下架内容 / `{ action: 'ignore' }` 驳回举报 |

**AI 预审（内容列表内置字段）**：`GET /admin/posts` 返回的每条内容附带 `aiReview`：

```json
{
  "id": "p7003",
  "author": "推广小王子",
  "text": "低价宠物药品，加微信 XXXXXX 私聊。",
  "state": "pending",
  "aiReview": {
    "hit": true,
    "words": ["低价", "微信", "私聊"],
    "kind": "广告导流",
    "suggestion": "reject"
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `hit` | 是否命中敏感词库 |
| `words` | 命中的词（最多返回 4 个） |
| `kind` | 违规归类：`广告导流` / `辱骂攻击` / `违法违规` |
| `suggestion` | AI 建议：`reject`（命中）/ `pass`（未命中，仅作参考） |

> 词库由 4.18.4 字典维护接口管理；AI 预审结论**仅供参考**，最终以人工审核为准——命中项标红提示，不自动下架。

---

### 4.19 钱包

#### 4.19.1 钱包余额 `●`

`GET /wallet`

```json
{
  "data": {
    "balance": 68.5,
    "currency": "CNY",
    "txns": [
      { "id": "t1", "amount": 30, "note": "充值", "time": "2026-10-12 10:00", "balanceAfter": 98.5 }
    ]
  }
}
```

#### 4.19.2 充值 `●`

`POST /wallet/topup`，`{ "amount": 50 }`（固定档位 30/50/100/200）。

服务端创建支付单并返回收银台参数（微信/支付宝）；演示环境直接入账。
`amount` 非法（非正数/超上限）返回 `code=42205`。

#### 4.19.3 提现 `●`

`POST /wallet/withdraw`，`{ "amount": 20 }`。

余额不足返回 `code=42206`；演示环境直接扣减并记流水。

> 钱包当前服务于问诊红包/退款场景；所有流水 `txns[]` 追加不可改，`amount>0` 入账、`<0` 出账。

---

## 5. WebSocket 实时协议

### 5.1 连接

```text
wss://{host}/ws?token={accessToken}
```

- 连接建立后服务端校验 token，失败则发送 `error` 帧并关闭。
- 客户端需实现心跳：每 25s 发送 `{ "type": "ping" }`，服务端回 `{ "type": "pong" }`。
- 断线重连采用退避策略（1s / 2s / 4s / 8s，上限 30s），重连成功后按时间戳增量拉取离线消息。

### 5.2 服务端推送帧

统一结构：

```json
{
  "type": "consult.message",
  "seq": 1024,
  "timestamp": 1760000000000,
  "data": {}
}
```

| type | 用途 | data |
| --- | --- | --- |
| `consult.message` | 问诊医生回复 | `{orderId, message}` |
| `consult.state` | 问诊单状态变更（接诊/结束） | `{orderId, state}` |
| `consult.call` | 通话呼入 | `{orderId, channel, token}` |
| `im.message` | IM 新消息 | `{conversationId, message}` |
| `notification` | 系统通知（公告/提醒） | `{title, body, level}` |
| `recognition.result` | 异步识别完成 | `{taskId, result}` |
| `error` | 错误 | `{code, message}` |

### 5.3 客户端发送帧

```json
{ "type": "ping" }
{ "type": "consult.typing", "data": { "orderId": "o1" } }
{ "type": "consult.subscribe", "data": { "orderId": "o1" } }
```

> 订阅机制：进入问诊室时订阅该 `orderId`，离开时 `consult.unsubscribe`，避免无用推送。

### 5.4 与轮询的取舍

毕设演示阶段，若 WebSocket 实现成本过高，可降级为「轮询 + 本地增量」：

```text
GET /consult/orders/{id}/messages?afterSeq=1024
```

但**医生接诊通知、通话呼入**建议必须实时。

---

## 6. 附录

### 附录 A：枚举字典

| 字典 | 取值 |
| --- | --- |
| `pet.species` | `cat` / `dog` / `other` |
| `pet.gender` | `公` / `母` |
| `health_record.kind` | `weight` / `diet` / `symptom` / `care` |
| `schedule.type` | `vaccine` / `deworm` / `check` / `weight` / `groom` / `other` |
| `schedule.state` | `overdue` / `today` / `soon` / `future` |
| `reminder.state` | `good` / `watch` / `overdue` |
| `announcement.level` | `event` / `warn` / `info` |
| `feedback.type` | `bug` / `feature` / `other` |
| `feedback.state` | `open` / `processing` / `resolved` |
| `consult_mode` | `text` / `voice` / `video` |
| `order.state` | `pending` / `replied` / `closed` |
| `message.type` | `user` / `doctor` / `system` / `rx` |
| `triage.level` | `emergency` / `urgent` / `home` |
| `report.type` | `ai` / `human` |
| `conversation.kind` | `vet` / `group` / `friend` |
| `favorite.kind` | `breed` / `post` / `tip` |
| `metric.state` | `good` / `watch` / `risk` |

**图标名**（前端 `AppIcon` 字典，后端下发 `icon` 字段时请沿用）：
`home` `camera` `paw` `chat` `user` `stethoscope` `heart` `plus` `send` `search` `bell` `signal`
`battery` `sparkle` `comment` `image` `phone` `check` `back` `bookmark` `heart-o` `x` `calendar-check`
`scale` `pill` `notes` `refresh` `location` `calendar` `flame` `mic` `share` `eye` `eye-off`
`wechat` `logout` `video` `star` `clock` `alert` `award` `wallet` `file` `filter` `verified`
`firstaid` `trendup`

### 附录 B：Mock → API 替换映射表

前端接入时按此表逐个替换 `apps/mobile/src/data/ops.js` 与 `mock.js` 的消费方式。

| 前端来源 | 替换为 | 说明 |
| --- | --- | --- |
| `mock.user` | `GET /users/me` | 也可取 `/home` 中的 `user` |
| `mock.pets` | `GET /pets` | |
| `mock.petTrends[petId]` | `GET /pets/{id}/health-trend` | |
| `mock.petReminders[petId]` | `GET /pets/{id}/reminders` | |
| `mock.petWeightHistory[petId]` | `GET /pets/{id}/weights` | |
| `mock.petSchedule` | `GET /schedule` | 服务端合并周期生成与自建条目 |
| `mock.scheduleTypes` | `GET /schedule/types` | |
| `ops.customScheduleItems()` | `GET /schedule?custom=true` | |
| `ops.addScheduleItem()` | `POST /schedule` | |
| `ops.toggleScheduleDone()` | `PATCH /schedule/{id}/done` | |
| `ops.removeScheduleItem()` | `DELETE /schedule/{id}` | |
| `ops.customRecords()` / `recordsOf()` | `GET /pets/{id}/records` | |
| `ops.addRecord()` | `POST /pets/{id}/records` | |
| `ops.removeRecord()` | `DELETE /records/{id}` | |
| `ops.activeAnnouncements()` | `GET /announcements?active=true` | |
| `ops.dismissAnnouncement()` | `POST /announcements/{id}/dismiss` | |
| `ops.submitFeedback()` | `POST /feedbacks` | |
| `ops.login()` / `logout()` / `getAuth()` | `POST /auth/login` 等 | 本地仅保留 token |
| `ops.isAuthed()` | 由 token 有效性判断 | 路由守卫改为校验 token + `401` 拦截 |
| `mock.recognitionSamples` | `POST /recognitions` | 真实 CV 模型 |
| `mock.breedLibrary` | `GET /breeds` / `GET /breeds/{id}` | |
| `mock.consultSeed` / `consultSuggestions` | `GET /consult/dictionary` | 可服务端下发引导语 |
| `mock.departments` | `GET /consult/departments` | |
| `mock.consultModes` | `GET /consult/modes` | 价格以后端为准 |
| `mock.bodyParts` / `durations` / `severities` / `accompanyOptions` | `GET /consult/dictionary` | |
| `triage.js scoreTriage()` | `POST /consult/triage` · `POST /consult/pre-consult` | 引擎逻辑移植到后端，输出结构保持一致 |
| `ops.aiQuota()` / `consumeAiQuota()` | `GET /consult/ai-quota` | 扣减在 `triage` 接口内部完成 |
| `mock.doctors` | `GET /doctors` / `GET /doctors/{id}` | |
| `ops.createConsultOrder()` | `POST /consult/orders` | |
| `ops.consultOrders()` / `orderById()` | `GET /consult/orders[/{id}]` | |
| `ops.appendOrderMessage()` | `POST /consult/orders/{id}/messages` | |
| `ops.closeOrder()` | `POST /consult/orders/{id}/close` | 服务端同时生成 human 报告 |
| `ops.rateOrder()` | `POST /consult/orders/{id}/rating` | |
| `ops.saveReport()` | `POST /consult/reports` | |
| `ops.reports()` / `reportById()` | `GET /consult/reports[/{id}]` | |
| `ops.archiveReport()` | `POST /consult/reports/{id}/archive` | |
| `ops.remindFromReport()` | `POST /consult/reports/{id}/remind` | |
| `report.exportReport()` | `GET /consult/reports/{id}/export` | |
| `mock.feed` / `commentsByPost` | `GET /posts` 系列 | |
| `mock.conversations` / `chatRooms` | `GET /conversations` 系列 | |
| `mock.favorites` | `GET /favorites` | |
| `mock.quickActions` / `tips` | `GET /home` | 可由运营后台配置 |

### 附录 C：前端实现建议

1. **统一请求层**：已提供零依赖实现 `apps/mobile/src/api/`（基于 `fetch`，无需安装 axios）：
   - `request.js` —— 统一信封解析、Bearer 注入、`401/20002` 静默刷新后重试、错误抛 `ApiError(code, message)`
   - `token.js` —— accessToken / refreshToken 存储与刷新
   - `index.js` —— 按模块导出的 API 集合（`authApi` / `petsApi` / `consultApi` …），函数名与路径已与本文档对齐
2. **联调代理**：`vite.config.js` 已配置 `/api` 代理，后端端口可用环境变量覆盖：

   ```bash
   VITE_PROXY_TARGET=http://localhost:8080 npm run dev
   ```

   线上部署时改为同源网关或配置 CORS 白名单。
3. **数据层切换开关**：可保留 `mock.js`，通过 `VITE_USE_MOCK=true` 回退到本地数据，便于后端未就绪时继续开发。
4. **不要信任前端计价**：问诊价格一律取 `GET /consult/modes` 与订单返回值。
5. **额度控制口径**：AI 分诊是否可用以服务端额度接口为准，前端仅做引导。
6. **幂等**：下单、支付、归档、提醒生成均需支持重复调用不产生副作用。

### 附录 D：安全与合规提示

- 宠物医疗属于专业领域，**所有 AI 结论必须显著标注为辅助参考**，报告中保留免责声明与紧急就医提示。
- 用户上传的宠物图片、问诊内容属敏感数据，需做访问控制，禁止越权读取他人病历。
- 医生资质信息需可追溯，建议在 `doctor` 表维护资质文件与审核状态。
- 生产环境应对接真实短信服务并对验证码接口做图形验证/人机校验，防止短信轰炸。
