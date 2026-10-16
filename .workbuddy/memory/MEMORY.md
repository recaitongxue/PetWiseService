# Petwise 项目长期备忘

## 技术栈
- app/：Vue 3 + Vite 5 + Vue Router（哈希路由，移动优先，440px 手机壳居中预览，面向 Capacitor 跨端打包）
- admin/：管理端（公告、反馈与 app 端通过 localStorage 键共享：petwise_announcements / petwise_feedbacks）
- **数据层（2026-10-16 定稿）**：视图只从 `src/api/data.js`（数据门面）取数，它调 `src/api/index.js` 的真实接口并归一成原 mock 形状
  - `src/data/ops.js` **已删除**（2026-10-16 清理，连同 mock.js/triage.js/useAsync.js/admin 的 data/ 目录）
  - 静态配置在 `src/data/static.js`（294 行，从 1057 行 mock.js 抽出）：quickActions/tips/consultSeed/consultSuggestions/departments/consultModes/bodyParts/durations/severities/accompanyOptions/symptomGroups/triageRules/recognitionSamples/galleryPool
  - 纯客户端能力在 `src/api/client.js`：短信每日频控、钱包流水、isAuthed
  - 同步→异步套路：mock 常量改 `ref`，`onMounted` 里加载，computed 给安全空形状兜底

## 布局铁律（踩过的坑）
- 外壳 .app-shell 必须用 height（100dvh）锁死而非 min-height；.app-main 必须有 min-height:0 —— 否则 flex 子项被内容撑高、整页滚动、底部 Dock 失效
- **底部 Dock 是 .app-shell 的静态 flex 项（2026-10-14 定稿）**：不再 position:absolute 悬浮，内容不被遮挡、导航不随内容滚动；.app-main padding-bottom 为 0，底部呼吸由各页 .screen 的 padding-bottom 负责
- **底栏定位一律用 --dock-h 令牌**：`bottom: calc(var(--dock-h) + env(safe-area-inset-bottom))`，禁止写死像素（历史上 78px/92px 并存导致底栏位置不统一）；--dock-h:71px 必须与 AppNav .dock 实测高度一致，改 Dock 内边距要同步
- 各页固定底栏清单：ChatRoom composer（静态 flex 项）、Consult composer+followups+disclaimer、ConsultationRoom composer、DoctorDetail paybar、Report bar、PreConsult nav、Community fab；DoctorDetail/Report/PreConsult 的 .screen 自带 128~132px 底部避让
- 短对话贴底对齐用「首个子元素 margin-top:auto」，不要 justify-content:flex-end（溢出时顶部不可滚的经典 flex 陷阱）
- 滚动容器是 .app-main 不是 window：切页需手动归零（App.vue 中 watch route.path）；vue-router scrollBehavior 对它无效
- vite.config 不要硬编码 hmr.clientPort（曾导致本地 HMR 完全失效）

## 共享实现约定（App 内）
- 6 位验证码输入：components/CodeInput.vue（Login + Account 共用，勿再手写分格）
- 短信发送频控：api/client.js 的 smsSendCount/bumpSmsSend/SMS_DAILY_MAX（按日+按号计数，键 petwise_sms_sent）
- 修改密码弹层唯一实现在 Account.vue（Profile 的入口只做跳转）

## 认证
- 路由 meta.public 放行（splash/login），其余被 beforeEach 拦截到 /login?redirect=
- 登录态 = JWT：petwise_access_token / petwise_refresh_token（api/token.js）；request.js 自动注入 Bearer，20002 时静默 refresh 重试一次
- 演示登录：任意 1[3-9]xxxxxxxxx 手机号 + 验证码 **888888**（后端 PW_SMS_DEBUG=true）

## cv/ 目录约定（2026-10 去重后定稿）
- 铁律：**每个能力只留一份实现**，狗/猫不允许出现结构相同、只有 import 不同的文件
- 分层：cv/common 共享内核（data / models / train / eval / export）+ cv/<kind>（dog、cat）只放数据适配器
- 物种约定（common/data/species.py 动态加载，目录扫描出 kind 列表）：
  - `cv/<kind>/src/data/dataset.py::build_loaders`
  - `cv/<kind>/src/data/labels.py::make_labels` + `CN_JSON`
  - 新增物种 = 建目录 + 这两个文件 + configs，内核与脚本零改动
- 唯一入口：`python -m common.train.run --kind dog|cat`、`common.data.make_labels --kind`、
  `common.export.to_onnx --kind`；日常用 `cv/scripts/{prepare,train,export}.sh <kind>`
- 物种特有的数据集参数**不写代码**：写在各自 dataset.yaml，由 cli 按 build_loaders 的签名+注解自动注入
- dog / cat 的包名都是 `src`：pytest 必须分目录跑；同进程连续加载要清 sys.modules 缓存

## 验证方式
- npx vite build 全量编译（mobile + admin 两个 app）
- 接口冒烟：`.venv/Scripts/python.exe .workbuddy/smoke_api.py` / `smoke_admin.py`（需后端在 8080）
- 浏览器 e2e（playwright-core 装在 `~/.workbuddy/binaries/node/workspace`，用本机 chrome）：
  `node .workbuddy/e2e_check.cjs`（移动端 13 页+登录+问诊）、`e2e_admin.cjs`（管理端 8 页）、
  `e2e_flows.cjs`（点赞/日程/聊天/识别/退出登录）、`e2e_layout.cjs`（dock 布局铁律）、
  `e2e_preconsult.cjs`（7 步向导）
- 注意：冒烟会消耗演示用户当日 AI 额度（3/日），问诊联调前先清 `ai_usage_daily` 当日记录
- cv：cd cv/dog、cv/cat 分别 pytest；`python cv/.workbuddy/smoke_train.py` 合成数据全流程冒烟

## 设计体系（2026-10 定稿，源自趋势调研）
- 方向：平静界面 Calm Interface + 低饱和大地色（暖纸白底 + 深松绿墨 + 珊瑚仅作强调）
- 分层靠发丝描边 --hairline（rgba(27,42,34,.07)）而非重阴影；阴影极轻
- 圆角 4 档：10/14/20/28 + pill；不要新增档位
- 渐变只用 3 主（ink/coral/sage）+ 2 低饱和辅色（peach/sand）
- 禁止：纸质噪点纹理、多团渐变光晕、纯黑重阴影、装饰性动效
- 微交互统一：按压 scale(0.978)、150–300ms、--ease-out
- 用户偏好：「高级、干净」= 做减法；新功能先问是否必要，宁可留白

## 参考项目
- E:\PetWise（旧毕设：Flask + Vant 移动端 + Element PC 端）：功能参考源，但 UI 不照搬
- PetWiseService 的 app 已含：识别 / 问诊 / 社区 / 消息 / 档案 / 日程 / 问诊记录 / 收藏

## 后端 services/api（2026-10-14 起，本地 MySQL 真实数据）
- **数据库**：本地 MySQL 9.7，root / 123456，端口 3306，库名 `petwise`（用户指定，勿改）
  - 连接串 `mysql+pymysql://root:123456@127.0.0.1:3306/petwise`（配置键 `PW_DATABASE_URL`）
  - 驱动已 psycopg → **pymysql**（用户要 MySQL 不是 Postgres）
- **运行**：`cd services/api && uv sync`（已装 pymysql/sqlalchemy）；`uv run uvicorn app.main:app --port 8080`
  - 建表+种子：`uv run python -m app.scripts.seed`（幂等，仅库空时灌；`--reset` 清空重灌）
  - 接口前缀 `/api/v1`，文档 `/docs`；本地演示鉴权调试码 **888888**（`PW_SMS_DEBUG=true`）
- **结构**：`app/db.py`（引擎+Session+get_db+create_all）、`app/models/*`（User/Pet/ScheduleItem/HealthRecord/Announcement/Feedback/Breed/Doctor/SmsCode）、`app/schemas/*`、`app/api/routers/*`（auth/users/pets/schedule/announcements/feedback/breeds/consult）
  - 响应统一 `ok()/paged()` 信封（app/core/envelope），错误统一 `AppError`+`ErrorCode`（app/core/errors）
  - 路由用 `def` 同步函数跑线程池（同步 SQLAlchemy）；当前以 create_all 建表，**生产需改 alembic**
- **首批真实接口**：登录/sms、users(me/preferences/blocked/balance/deactivate)、pets(CRUD+health)、schedule(CRUD+done+/home/reminders 跨宠物聚合)、announcements、feedback、breeds、consult(modes/departments/doctors)
- **演示账号**：13800138000（昵称林小满，宠物 麻薯/豆豆），验证码 888888
- **已知坑**：`errors.py` 的 `http_status` 原实现用 `dict.get(code, _HTTP_STATUS[code//10000*10000])`，因 get 的 default 参数会被**先求值**导致任何码都 KeyError —— 已改为先 get 再 `.get(segment, 500)` 兜底
- **管理端全栈（2026-10-16 完成）**：`apps/admin` 8 视图全迁到真实接口（原 localStorage 清零）
  - 后端 `app/api/routers/admin.py`（prefix `/admin`，AdminUser 依赖，非 admin 返 20004）：overview / 公告 CRUD / 反馈列表+处理 / 用户列表+改角色 / 问诊单 / 识别审核 / 举报审核 / 设置读写
  - 新模型：`PostReport`（social.py，举报落库）、`Setting`（extra.py，key-value 设置，默认值在 admin.py `_DEFAULT_SETTINGS`）
  - 管理员账号：**13900000000**（role=admin，验证码 888888）
  - 管理端 dev 端口 **5174**（`/api` 代理同后端）；`.workbuddy/smoke_admin.py` 全绿含非 admin 拦截验证
  - `/health`、`/health/ready` 故意不带 `/api/v1` 前缀（k8s 探针）
- **前端已全量接后端（2026-10-16）**：23 个视图全部走真实接口；`data/ops.js` 已删除引用
- **联调验证**：`.workbuddy/smoke_api.py`（登录 + 30+ 接口 + 写路径，失败项 0）；前端 dev 5173 经 /api 代理到 8080
- **后端信封坑**：`paged()` 内部已包 `ok()`，**不可再套 ok()**（否则前端拿到信封而非 {list}，`r.list` undefined → .map 崩）；且 total/page/page_size 是关键字参数，位置传参会 500
- **踩坑**：uv sync 因 hatchling 找不到打包目录报错 → pyproject 补 `[tool.hatch.build.targets.wheel] packages=["app"]`；`SMS_DEBUG` 必须定义在 Settings 里否则调试码不生效
