# PetWise 功能文档

> 面向产品/开发/答辩的功能说明：系统**有哪些功能**、**每个功能怎么走**、**边界与状态**、**当前实现到哪一步**。
>
> 版本：v1.1 ｜ 更新日期：2026-10-14 ｜ 对应代码基线：`main` 当前提交

## 目录

- [0. 阅读指南](#0-阅读指南)
- [1. 产品概览](#1-产品概览)
- [2. C 端 App 功能（apps/mobile）](#2-c-端-app-功能appsmobile)
- [3. 管理端功能（apps/admin）](#3-管理端功能appsadmin)
- [4. AI 能力：品种识别与问诊智能体](#4-ai-能力品种识别与问诊智能体)
- [5. 横切能力](#5-横切能力)
- [6. 功能 → 代码 → 接口 速查表](#6-功能--代码--接口-速查表)
- [7. 已知限制与占位清单](#7-已知限制与占位清单)
- [8. 附录：本地持久化键名全集](#8-附录本地持久化键名全集)

---

## 0. 阅读指南

### 0.1 本文档与其它文档的分工

| 文档 | 回答什么问题 | 什么时候看 |
| --- | --- | --- |
| **本文档 FEATURES.md** | 有哪些功能？怎么用？流程是什么？实现到哪一步？ | 了解产品全貌、写需求/验收、答辩讲功能 |
| [API.md](API.md) | 接口字段、请求体、错误码、WebSocket 协议 | 联调、写后端 router、写前端 API 封装 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 目录怎么切、分层纪律、服务边界、降级方案 | 加目录、加服务、答辩讲架构 |
| [REPO-STRUCTURE.md](REPO-STRUCTURE.md) | 每个文件夹放什么 | 找文件、放新文件 |
| [FEATURE-ROADMAP.md](FEATURE-ROADMAP.md) | 未来还能做什么、竞品调研、P0–P5 排期 | 规划下一阶段 |

一句话：**架构讲"怎么切"，API 讲"怎么连"，本文档讲"做什么、怎么用"。**

### 0.2 实现状态图例

文档里每个功能都带状态标记，含义严格如下：

| 标记 | 含义 | 说明 |
| --- | --- | --- |
| ✅ **已实现** | 业务逻辑完整落地，含本地持久化/真实算法 | 换数据源后可直接投产 |
| 🟡 **演示实现** | 逻辑跑通、数据包 mock、可能用 `setTimeout` 模拟延迟 | 交互完整但不是真实后端/真实模型/真实 LLM |
| ⬜ **占位** | 只有 UI 或弹 Toast，无副作用 | 明确未实现，避免被误认为已完成 |

> 截至本文档版本：**全部 C 端页面与管理端页面均处于「🟡 演示实现」或「⬜ 占位」**，数据来自 `data/mock.js` + `localStorage`；后端三个服务中，`vision` 的模型产物待训练、`agent` 未配置 LLM 密钥时走规则基线。详见 [第 7 节](#7-已知限制与占位清单)。

### 0.3 术语

| 术语 | 含义 |
| --- | --- |
| **主诉** | 用户对宠物症状的原始文字描述 |
| **分诊 / triage** | 把主诉映射为 `emergency / urgent / home` 三档严重程度，并给出建议 |
| **预问诊** | 跳过自由对话，用 7 步结构化问卷一次性采齐症状信息 |
| **病例摘要** | AI 问诊转真人医生时，自动沉淀的结构化病情说明 |
| **拒识** | 识别置信度低于阈值时，坦承"未识别到品种"而非强行给结果 |
| **降级** | 下游 AI 服务不可用时，主链路不失败、以次优结果继续 |

---

## 1. 产品概览

### 1.1 一句话定位

**用计算机视觉读懂宠物的"外表"（品种/体态），用大模型读懂宠物的"不适"（症状/风险），再把结论沉淀成一份可带给线下医生的健康档案。**

差异化打法：**拍照识别 → AI 分诊 → 真人问诊 → 沉淀档案** 形成闭环，而不是三个互不相干的功能。

### 1.2 用户角色

| 角色 | 载体 | 能做什么 | 当前登录方式 |
| --- | --- | --- | --- |
| **宠主** | `apps/mobile`（C 端 App，可 Capacitor 打包） | 识别、问诊、档案、日程、社区、消息、反馈 | 🟡 手机号 `1[3-9]\d{9}` + 任意 6 位验证码，写 `petwise_auth` |
| **平台运营** | `apps/admin`（Web 后台） | 看板、用户、识别复核、内容审核、问诊记录、公告、反馈、设置 | 🟡 `admin / petwise`，写 `petwise_admin_auth='1'` |
| **兽医（医生）** | 仅作为数据与问诊对象存在，**无独立登录端** | 出现在 C 端医生列表/问诊室；管理端只能查看问诊记录 | ⬜ 未实现医生后台 |

### 1.3 端与服务清单

| 部署单元 | 端口 | 职责 | 状态 |
| --- | --- | --- | --- |
| `apps/mobile` | 5173 | C 端产品面 | 🟡 mock 数据 + localStorage |
| `apps/admin` | 5174 | 运营后台 | 🟡 mock 数据 + localStorage |
| `services/api` | 8080 | 唯一对外网关，持有全部业务数据 | 🟡 骨架完整（信封/鉴权/中间件/健康检查/客户端），业务 router 待补 |
| `services/vision` | 8081 | 无状态视觉推理，仅对内 | ✅ 推理链路完整；⬜ 缺 `cv/artifacts` 权重，当前恒降级 |
| `services/agent` | 8082 | 问诊智能体 + 知识库 | ✅ 链路/知识库/护栏完整；🟡 无 LLM 密钥时走规则基线 |
| `cv/` | 离线 | 模型训练 → 导出 ONNX → 交付 `vision` | ✅ 狗/猫两条训练流水线已就绪，待 GPU 训练 |

### 1.4 请求链路

```
apps/mobile ─┐
             ├─▶ nginx ──▶ services/api ──┬──▶ services/vision ──▶ model-dog/cat-vN.onnx
apps/admin ──┘                            └──▶ services/agent  ──▶ pgvector 知识库 + LLM
```

`services/api` 是**唯一对外网关**；`vision` / `agent` 不暴露给客户端，只接受携带 `X-Internal-Token` 的内部调用。

### 1.5 功能总览

| 一级功能 | 二级功能 | 载体 | 状态 | 一句话 |
| --- | --- | --- | --- | --- |
| **启动与登录** | 冷启动分流、手机验证码登录 | mobile | 🟡 | 未登录访问任何业务页会被弹回登录并记住回跳目标 |
| **首页概览** | 健康分、今日提醒、快捷服务、周趋势、公告 | mobile | 🟡 | 多宠物的一屏总览，是所有主功能的分发中枢 |
| **拍照识别** | 拍摄/选图识别、置信度、识别记录 | mobile + vision + cv | 🟡 | ✅推理链路齐备，⏳等待 cv 训练产物 |
| **品种百科** | 性格/易患病/护理要点 | mobile | 🟡 | 把识别结果延伸成知识，并一键发起问诊 |
| **宠物档案** | 体重趋势、免疫日程、健康记录、手动录入 | mobile | 🟡 | 一只宠物的完整时间轴，报告可沉淀到这里 |
| **日程与提醒** | 跨宠物日程、逾期标记、完成/撤销、自建 | mobile | 🟡 | 待办/已完成两分，勾选与自建真实落盘 |
| **AI 智能问诊** | 多轮对话、分诊卡、随访追问、病例摘要 | mobile + agent | 🟡 | 3 次/日免费额度，超限引导转真人而非拒绝服务 |
| **结构化预问诊** | 7 步问卷、可解释评分 | mobile + agent | 🟡 | 高危信号一票否决判急症，其余加权分级且逐项可回溯 |
| **真人医生问诊** | 科室筛选、医生详情、下单、问诊室、评价 | mobile | 🟡 | 图文 19 / 电话 39 / 视频 59，端到端闭环到本地报告 |
| **问诊报告** | 报告详情、存入档案、转日程提醒、转诊 | mobile | 🟡 | 把一次问诊固化成可带走、可执行的结构化产物 |
| **问诊记录** | 三源聚合（AI / 真人 / 报告） | mobile | 🟡 | 统一回看入口，有报告优先进报告页 |
| **宠物社区** | 信息流、话题筛选、发布、点赞评论 | mobile | 🟡 | 发布内容不持久化（演示态） |
| **即时消息** | 会话列表、聊天室 | mobile | 🟡 | 脚本化自动回复，未接 WebSocket |
| **我的** | 账号、宠物、收藏、反馈、退出 | mobile | 🟡 | 反馈与管理端构成真实双端闭环 |
| **运营后台** | 看板/用户/识别复核/审核/问诊/公告/反馈/设置 | admin | 🟡 | 公告与反馈双端闭环，其余为静态数据 |
| **CV 模型** | 训练 → 评测 → 导出 ONNX | cv | ✅ | dog 130 类 / cat 60 类，两套独立模型 + 物种路由 |
| **知识库 RAG** | 灌库、混合检索、重排、溯源 | agent | ✅ | 支持 hash / 本地 / OpenAI 三种 embedding，零依赖可跑 |

---

## 2. C 端 App 功能（apps/mobile）

> 所有页面在 `apps/mobile/src/views/`，共 21 条路由（哈希路由，便于静态托管与 Capacitor `file://` 运行）。

### 2.0 全局框架

| 能力 | 实现要点 | 状态 |
| --- | --- | --- |
| **手机外壳** | `.app-shell` 锁 100dvh、440px 居中；状态栏时钟每 30s 走一次；页面切换 `<transition name="page" mode="out-in">` | ✅ |
| **登录拦截** | `router.beforeEach`：`meta.public` 放行；否则未登录跳 `/login?redirect=<原路径>`，登录后 `replace` 回跳 | ✅ |
| **底部 Dock** | 5 入口：今日 / 社区 / **问诊（中央 FAB）** / 消息 / 我的；`splash`、`login` 两页隐藏（`meta.bare`）。**嵌入式布局**：Dock 是 `.app-shell` 的静态 flex 项（顶部发丝边 + 毛玻璃），不再悬浮遮挡内容——内容区在导航上方自然收住、导航不随内容滚动 | ✅ |
| **Dock 高亮域匹配** | `route.path === x` 或 `path.startsWith(x + '/')`；问诊域含 `/consult /preconsult /doctors /doctor /consultation /report /records`；聊天详情页仍高亮"消息"；`/account` 归"我的"域 | ✅ |
| **底栏定位令牌** | 各页固定底栏（聊天/问诊输入栏、医生 paybar、报告 bar、步骤 nav）一律 `bottom: calc(var(--dock-h) + env(safe-area-inset-bottom))`，与 Dock 严丝合缝；`--dock-h: 71px` 必须与 Dock 实测高度一致。悬浮 FAB（社区发布）同样用该令牌。**禁止再写死像素值**（历史上 78px/92px 并存导致底栏位置不统一） | ✅ |
| **短对话贴底对齐** | 聊天/问诊对话区消息不足一屏时贴底展示（首个子元素 `margin-top:auto`，规避 `justify-content:flex-end` 的溢出滚动陷阱），与主流 IM 一致 | ✅ |
| **滚动归零** | 滚动容器是 `.app-main` 不是 window，`watch(route.path)` 手动归零（`scrollBehavior` 对它无效） | ✅ |
| **全局 Toast** | `composables/toast.js` 单例，默认 2200ms；`success` 绿 / `warn` 黄 / `default·info` 深墨 | ✅ |
| **健康分环** | `HealthRing.vue`，唯一分级阈值：`≥85` 绿（good）、`≥70` 黄（watch）、`<70` 红（alert） | ✅ |
| **统一请求层** | `api/request.js`：信封解析、`Bearer` 注入、`code=20002` 静默 refresh 重试一次、`ApiError`；`VITE_USE_MOCK` 控制是否仍走本地数据 | ✅ 已就绪，**⏳未接线** |

**API 封装已备好但未启用**：`api/index.js` 导出 `authApi / petsApi / scheduleApi / homeApi / contentApi / recognitionApi / consultApi / communityApi / imApi / fileApi / adminApi` 共 11 组、60+ 方法，路径与 [API.md](API.md) 严格一致。当前所有页面仍 `import` 自 `@/data/mock` 与 `@/data/ops`。

---

### 2.1 启动与登录

**功能**：冷启动分流 + 手机号登录（验证�� / 密码双模式）。 🟡

**路由**：`/`（splash，`public`）→ `/login`（`public`）→ 回跳目标或 `/home`

**流程**

1. `Splash.vue` 同步读取 `isAuthed()`：已登录按钮文案「进入 Petwise」，否则「开始使用」→ `replace` 到 `/home` 或 `/login`
2. `Login.vue` 两种 Tab：验证码 / 密码；手机号正则 `/^1[3-9]\d{9}$/`，验证码 `/^\d{6}$/`，密码 ≥6 位
3. 「获取验证码」→ 60s 倒计时 + Toast「验证码已发送（演示：任意 6 位数字）」
4. 提交 → `setTimeout 700ms` → `login({phone, mode})` 写 `petwise_auth` → Toast「欢迎回来，138\*\*\*\*8888」→ 回跳

**安全加固（2026-10-14）**

| 项 | 实现 |
| --- | --- |
| 验证码输入 | 6 个分格 box，自动跳格、退格回跳、粘贴自动分发；仅接受数字 |
| 发送频控 | 60s 冷却 + **每日 5 次上限**（`petwise_sms_sent` 按日计数持久化），超限禁用按钮并 Toast 说明 |
| 手机号清洗 | `@input` 实时剥离非数字字符，防粘贴注入 |
| 密码强度 | 密码登录时实时评分 0–3（weak/mid/strong + 文案），仅前端提示不阻断 |
| 输入校验 | 全部走正则白名单，无 `v-html`、无动态拼接选择器，杜绝注入面 |

**规则与分支**

| 分支 | 行为 |
| --- | --- |
| 未勾选协议 | Toast「请先勾选并同意用户协议」，不发请求 |
| 微信登录 | ⬜ Toast「微信授权为演示占位，请先用手机号登录」 |
| 注册 / 忘记密码 / 协议链接 | ⬜ 均为 Toast 占位 |
| 加载态 | 按钮显示 spinner 且 disabled |

**数据源**：`ops.login()` → 最终映射 `authApi.sendCode()` / `authApi.login()` / `authApi.me()`

---

### 2.2 首页 `Home.vue`（`/home`）

**功能**：当前宠物的一屏总览 + 全功能分发中枢。 🟡

**页面区块（自上而下）**

| 区块 | 内容 | 规则 |
| --- | --- | --- |
| 头部 | 问候语 + 用户名 + 日期（`周三 · 10.14`）+ 通知铃铛 | 问候按小时分档，**每档多句随机**（早安/午安/下午好/晚安/夜深了各 3–4 句）；周一「新的一周」、周五「周五特调」彩蛋；副标题按小时给陪伴文案（如「午间陪它玩十分钟吧」） |
| 平台公告 | 折叠卡，展开看全部 | `active===true` 且不在 `petwise_ann_dismissed` 中；「知道了，不再显示」写 dismissed 集合 |
| 宠物切换 | Tab + 头像 | 切换后 hero / 趋势两处联动（**不再联动提醒区**，提醒区默认看全部宠物，见①） |
| 主角卡 | 名称、品种·年龄·性别、疫苗 chip、健康分环、标签语 | 健康分直接取档案静态值（演示：麻薯 86→绿、豆豆 78→黄） |
| 今日贴士 | 轮播 | `tipIndex = (tipIndex+1) % tips.length` |
| ① 今日提醒 | **大卡**：统计条 + 宠物筛选 chips + 提醒列表 | 聚合**全部宠物**的真实日程（`petSchedule` 内置 + `customScheduleItems` 自建，跨宠物合并）；统计 = 已逾期 / 今天待办 / 已完成（全量口径，与列表一致）；筛选 chips「全部 + 每只宠物」（带头像与待办数角标），默认「全部」，列表项在全部视图下带**宠物名标签**；`diff<=0` 的前 4 条按日期升序，超出显示「还有 N 条待办」→ `/schedule`；点「完成了」调 `toggleScheduleDone` **真实持久化** |
| ② 快捷服务 | 单行 4 列 tool-strip | 智能问诊（`AI 免费 3 次/日`）、识别、社区、档案——**由 2×2 Bento 磁贴弱化为图标横排**，视觉权重让位给今日提醒 |
| ③ 本周趋势 | 平均分大数字 + 7 根柱状图 | 平均分 = 7 天均值（演示：87 / 83）；柱色按 `label` 分档：`优`→珊瑚、`需关注`→琥珀、其余→松绿；柱高 = `value%` |
| 社区引流 | Banner | → `/community` |

**空态与异常**：公告区条件渲染（无公告整块不显示）；全页无加载态、无错误态。

**数据源 → 接口映射**

| 当前 | 最终接口 |
| --- | --- |
| `mock.pets` | `GET /pets` |
| `mock.petTrends[id]` | `GET /pets/{id}/health-trend?week=` |
| `mock.petReminders[id]` | `GET /pets/{id}/reminders?date=` |
| `ops.activeAnnouncements()` | `GET /announcements?active=true` |
| `ops.dismissAnnouncement(id)` | `POST /announcements/{id}/dismiss` |
| `mock.quickActions / tips` | `GET /home?petId=`（建议改由运营后台配置） |

---

### 2.3 拍照识别 `Recognize.vue`（`/recognize`）

**功能**：拍照/选图 → 识别猫狗品种 → top1 品种档案介绍 + top3 备选 → 可百科、可问 AI、可手动纠正。 🟡（识别结果来自 mock，⏳待接 vision）

**流程**

1. 点快门 → `runScan()` → `scanning=true` → **1600ms** 后出结果
2. 点「从相册选择」→ 真实 `<input type=file>` → `URL.createObjectURL` 预览 → `runScan()`
3. 点示例库卡片 → 立即出结果（无延迟）
4. 结果页：品种 hero（名称 + 拉丁名 + 置信度条）→ 模型备选 chips（top3）→ **top1 品种档案**（原产地 / 寿命体重 / 性格 chips / 喂食建议前 2 条）→ 操作（重新识别 / 保存记录 / 品种百科 / 问问 AI）→ 「识别不准？手动纠正品种」

**取景框四态互斥**：真实照片 → 「将宠物放入框内」→ 「品种识别中…」+ 扫描线动画 → 识别结果插图。
`scanning` 期间快门与「重新识别」disabled。

> **模型只做品种识别**：cv 两个模型均为猫狗品种分类，不输出体态/健康指标——识别结果页不再展示任何健康项，所有饲养建议均来自品种库查表（与百科同源）。

**手动纠正与数据回流（核心闭环）**

```
用户认为识别不准 → 点「识别不准？手动纠正品种」
  → 未保存过的结果先自动保存记录
  → 底部弹层：同物种品种库（带搜索）中选择正确品种
  → correctRecognition(id, breed) → status='review'，写 petwise_recognitions
  → 管理端「识别记录」看到「纠正待审核」→ 通过 / 驳回
  → 通过（approved）→ 计入训练数据集，可导出 JSON（image_ref + 人工标签）
  → 驳回（rejected）→ 展示回模型原预测
```

**识别记录**（`petwise_recognitions`，持久化，管理端共用同一键）：

| 字段 | 说明 |
| --- | --- |
| `predicted` / `corrected` | 模型 top1 / 用户纠正后的品种（`corrected` 非空时列表显示「纠正自 X」） |
| `status` | `done` 未纠正 / `review` 纠正待审核 / `approved` 已采纳 / `rejected` 已驳回 |
| `imageRef` | 图片来源（演示标记；接后端后为对象存储 key） |

**数据源 → 接口映射**

| 当前 | 最终接口 |
| --- | --- |
| `mock.recognitionSamples` | `POST /recognitions`（multipart，真实调用 vision，含 alternatives top3） |
| `petwise_recognitions` | `GET /recognitions`、`POST /recognitions/{id}/correction` |
| `mock.breedLibrary` | `GET /breeds`、`GET /breeds/{id}`（含 feeding / aiPrompts） |

---

### 2.4 品种百科 `BreedDetail.vue`（`/breed/:id`）

**功能**：把识别结果延伸成品种知识页，与识别、AI 问诊双向联动。 🟡

- 查表顺序：`id` 精确匹配 → 否则 `name` 匹配；都未命中显示「没有找到这个品种，去识别看看」
- 区块：hero（插图 + 中文名 + 拉丁名 + 科属 + 原产地）、体重区间 / 预期寿命双栏、**01 性格特质** chips、**02 易患问题** 列表、**03 护理要点**、**04 喂食建议**（编号列表）、**AI 快捷提问卡**、底部双 CTA
- **AI 快捷提问**：每个品种 3 个预置问题（如「柯基腰椎脆弱，日常生活中怎么保护？」）→ 点击以 `{ pet: <品种名>, note: <问题原文> }` 进入 AI 问诊，知识库补充该品种语料后作答（RAG 联动）
- 底部 CTA：「就这个品种问一问」（进入问诊）+「拍一张识别看看」（回到识别页，识别→百科闭环）
- 演示库 6 个品种：英国短毛猫 / 柯基犬 / 布偶猫 / 金毛寻回犬 / 中华田园猫 / 暹罗猫
- 支持收藏（入口在其它页）

---

### 2.5 宠物档案 `PetProfile.vue`（`/pet/:id`）

**功能**：单宠完整健康档案 + 手动录入体重/饮食/症状/护理。 ✅（含真实 localStorage 落盘）

**流程与录入**

1. 入口：首页「健康档案」chip、我的 → 宠物卡片
2. 「＋ 记录体重」预填当前体重；健康记录区「＋ 添加」默认 `care` 类型
3. 类型 chip 共 4 种：`weight 体重 / diet 饮食 / symptom 症状 / care 护理`；仅 `weight` 显示数字输入框（step 0.1）
4. 保存条件：`canSave = form.date && (kind==='weight' ? !!form.value : !!form.note.trim())`
5. 自定义记录可删除（仅 `custom===true` 显示 ×）；Toast「体重已记录，趋势图已更新」/「记录已保存」/「记录已删除」

**体重趋势合成算法**（真实实现）

```
1. base ← mock.petWeightHistory[petId] 浅拷贝
2. custom ← 本地记录中 kind==='weight' 且 value 非空，按 date 升序
3. 归月：同月多条取最新一条（byMonth[m] = value）
4. 回写：base 中同月则覆盖，否则 push
5. 最终按月升序排序
6. 柱高 barH(w) = round(w / maxW * 100)%   ← 相对最大值归一化
```

**趋势文案阈值**：`diff > 0.05` →「较上月略增」；`diff < -0.05` →「较上月略减」；否则「保持稳定」；数据量 `<2` →「数据不足」。
`diff≠0` 时文案标黄（watch），否则标绿（good）。

**健康记录时间轴**：`[ ...用户录入(永远置顶), 3 条内置记录 ]`。内置项：
① 下次疫苗提醒（watch）② 体态评估（按物种分支文案，good）③ 驱虫完成（good）。
用户录入映射：`title = 类型中文名`；`desc = 体重类为「体重 X kg · 备注」，其余取备注`；**`kind==='symptom'` 自动标黄**。

**空态**：宠物不存在 → 整块不渲染，显示「未找到该宠物档案。」

**持久化**：录入/删除写 `petwise_pet_records`（跨刷新保留，且与报告归档共用同一键）。

**接口映射**：`GET /pets/{id}`、`GET /pets/{id}/weights?months=6`、`POST /pets/{id}/weights`、`GET|POST /pets/{id}/records`、`DELETE /records/{id}`

---

### 2.6 日程与提醒 `Schedule.vue`（`/schedule`）

**功能**：跨宠物的免疫/驱虫/体检/洗护提醒总表 + **AI 一键生成计划** + 随手备忘录。 🟡（勾选与自建真实落盘）

**交互**

- 筛选 chip：全部 + 每只宠物；右上 `+` 新建，**新建时归属宠物继承当前筛选**（全部时取第一只）
- 8 类类型：疫苗 `vaccine` / 驱虫 `deworm` / 体检 `check` / 称重 `weight` / 洗护 `groom` / 喂食 `feed` / 备忘 `memo` / 自定义 `other`
- 点 ✓ 完成 → Toast「已完成「标题」」；已完成区的「撤销」→ Toast「已撤销「标题」」并回到待办
- 时间轴项展示 `time`（bell 图标）+ `cycle` 周期 + `note` 备注

**AI 一键设置日程（核心新增）**

```
入口：渐变卡「AI 一键设置日程」→ 弹层
  1. 选择宠物（大卡单选）
  2. AI 分步思考动画（4 步 × 520ms：分析物种年龄 → 匹配免疫周期 → 推算驱虫间隔 → 生成计划）
  3. 展示推荐计划列表（可勾选，默认全选）
  4. 「一键添加 N 条日程」→ 按 title 去重跳过已存在项 → Toast「已添加 N 条，跳过 M 条重复」
```

计划由 `mock.aiSchedulePlan(pet)` 按物种/年龄/`nextVaccine` 生成 8 条：体外驱虫（7 天后/每月一次）、
体内驱虫（14 天后/每季一次）、年度疫苗、年度体检、洗护梳毛、体重复测、早餐 08:00、晚餐 18:00，
每条带 `cycle` 与 `note`。接后端后对应 `POST /schedule/ai-plan` + `POST /schedule/batch`（见 API.md §4.4.8）。

**备忘录（输入即存）**

- 日程页内独立分区，**无日期、不参与到期计算**，按置顶优先 + 创建时间倒序
- 输入框回车/失焦即写 `petwise_memos`；支持置顶（pin）与删除
- 与日程条目共享宠物归属概念，但数据层完全独立

**分组与到期规则**

```
数据来源 = 内置 petSchedule(petId 分组) + 自建 customScheduleItems
过滤 → 计算 diff/overdue/dateText/done → 按 date 升序 → 按 done 切「待办 / 已完成」
⚠ 不按日期分组；逾期不单独成组，只在待办里加「逾期」红标

diff = Math.round((new Date(date) - new Date()) / 86400000)
overdue = diff < 0
dateText:
  diff===0 → 今天 10.14      diff===1 → 明天 10.15      diff===2 → 后天 10.16
  diff<0   → 10.11（3 天前） diff<=7  → 10.19（5 天后） 其它 → 10.19
```

**概览四宫格**：待办 / 已逾期（>0 时数字转红）/ 已完成 / 备忘数。
**空态**：「这只宠物暂无日程，点右上角 + 添加一条。」（⚠ 筛选为「全部」时也显示这句，文案待优化）

**持久化**：`petwise_schedule_done`（完成的日程 id 数组）、`petwise_schedule_custom`（自建日程）、`petwise_memos`（备忘录）。

**接口映射**：`GET /schedule?...` / `GET /schedule/types` / `POST /schedule` / `PATCH /schedule/{id}/done` / `DELETE /schedule/{id}` / `POST /schedule/ai-plan` / `POST /schedule/batch` / `GET|POST /memo` / `PATCH|DELETE /memo/{id}`

---

### 2.7 AI 智能问诊 `Consult.vue`（`/consult/ai`）

**问诊中心 `ConsultHub.vue`（`/consult`）——问诊域总入口**

| 区块 | 内容 |
| --- | --- |
| 限免条 | 「AI 问诊限时免费中」渐变条，点击进 AI 问诊 |
| 问诊对象卡 | 当前宠物档案速览：健康分 + 疫苗到期日 → `/pet/:id` |
| RAG 高频问题 | 6 条预置问题（`ragQuestions`）→ `askAI()` 跳 `/consult/ai?q=` 并**自动发送** |
| 科室直达 | 六科室 chips（猫科内科 / 犬科内科 / 外科 / 皮肤科 / 异宠专科 / 影像科）→ `/doctors?dept=` |
| 最近报告 | 最多 2 条历史问诊报告 → `/report/:id` |
| 辅助工具 | 结构化预问诊 / 问诊记录 / 急诊指南三行入口 |

**功能**：围绕主诉的多轮对话式分诊，必要时升级为分诊卡并引导转真人。 🟡（消息脚本化，⏳待接 agent SSE）

**入口（4 个来源都带上下文）**

| 来源 | 携带 query |
| --- | --- |
| 首页快捷服务 | 无 |
| 识别结果「就结果问医生」 | `{ pet: 品种名, note: 识别提示 }` |
| 宠物档案「智能问诊」 | `{ pet: 宠物名, note: 品种·年龄·体重 }` |
| 品种百科 CTA | `{ pet: 品种名, note: '<品种>饲养与健康管理咨询' }` |

带上下文进入时，AI 首条即说：「我已了解你刚识别的是「X」。…你想进一步确认哪方面？我帮你分析。」
> 组件复用处理：`watch(() => route.query.pet)`，同名组件再次带参进入时同步上下文并重发问候。

**单轮时序（真实实现）**

```
用户点发送
  ├─ 守卫1：输入为空 或 typing 中 → 直接 return
  └─ 守卫2：quota.left <= 0 → Toast「今日 AI 免费次数已用完…」+ 直接跳医生列表
                              （不产生消息、不扣额度 —— 引导转真人而非拒绝服务）
     ↓
push({role:'me'}) → 清空 input/followups → scrollToEnd → typing = true
     ↓ 1300ms
  ├─ 命中关键词规则 → 生成【分诊卡】消息 kind:'triage'
  └─ 否则           → 生成【文本】消息 + 3 个随访 chip
     ↓
consumeAiQuota()   ← 额度在「回复生成之后」扣除
scrollToEnd
```

> ⚠ **当前不是真流式**：分 typing 占位 + 一次性插入。agent 侧已提供 SSE（`/internal/v1/triage/stream`），接线后可替换为增量渲染。

**消息结构**

```js
// 普通气泡
{ role: 'me' | 'ai', text, time: 'HH:mm' }
// 分诊卡（渲染为 TriageCard）
{ role: 'ai', kind: 'triage', time, triage: {
    level, label, short, advice, causes[], actions[], confidence, dept } }
```

**追问 chip 三类**

1. **症状快捷标签**：4 组 × 4 项（消化 / 皮肤 / 头颈 / 全身），选中后自动拼进输入框（`input = picked.join('、')`）
2. **推荐问题**：如「狗狗一直挠耳朵是怎么回事？」「幼猫疫苗时间表」
3. **随访建议**：命中分诊规则 → `['这种情况要立刻去医院吗','现在能做些什么','转真人医生看看']`；
   未命中按关键词生成（耳朵 / 食欲 / 疫苗 / 皮肤 / 兜底五套）

**提示与告警**

| UI | 触发 | 文案 |
| --- | --- | --- |
| 上下文横幅 | `ctx.pet` 非空 | 「已关联识别结果：X」（可 × 清除） |
| 急诊告警条 | `lastTriage.level === 'emergency'` | 「检测到疑似急症信号」/「<short> · 线上问诊会延误治疗」+「急诊医生」按钮 |
| 额度条 | 常驻 | 「今日 AI 免费问诊剩余 **n/3** 次」+「升级真人」 |
| 免责声明 | 固定底部 | 「AI 建议仅供参考，不能替代执业兽医的当面诊断。紧急情况请立即就医。」 |

**转真人时的病例摘要**：`goDoctors()` 把 `{petId, petName, species, breed, age, weight, gender, complaints[], symptoms[], triage}` 写入 `sessionStorage['petwise_case_summary']`，医生列表/详情页读取并展示 —— 用户不必重述病情。

**RAG 品种知识注入（2026-10-14）**

```
breedDoc = breedLibrary.find(b => b.name === curPet.breed)   // 按当前宠物品种检索
  → AI 回复追加「品种知识」段：易患问题 + 护理要点（来自品种档案）
  → 分诊卡消息携带 cite / citeBreedId，模板渲染「参考知识库」行 + 跳 /breed/:id 链接
```

检索不到品种（未收录）时静默跳过，**不编造引用**。对应后端约定见 API.md §4.10.2 `rag` 参数与 `cite` 字段。

**档案导入（从档案导入近期变化）**

- 入口：问诊页「从档案导入」按钮 → 弹层三源勾选：**健康档案记录**（`recordsOf`）、**识别记录**（`recognitionHistory`）、**历史问诊报告**（`impReports`）
- 确认后推入一条 `kind:'context'` 消息卡（渲染为档案卡片，不计入用户输入），AI 随后给出**结合品种知识的回复**
- 预问诊页同样支持：STEP 1「从档案导入近期变化」勾选后，生成报告时写入 `chief.records`（`{kind,label,value,date,note}`），报告页渲染为「近期变化（来自健康档案）」时间线

**占位能力**：⬜ 图片上传 `attach()` 为 1200ms 模拟，未真实接收/解析图片。

---

### 2.8 结构化预问诊 `PreConsult.vue`（`/preconsult`）

**功能**：跳过对话，7 步问卷一次性采齐症状，产出可解释评分 + 落一份报告。 ✅（算法完整，⏳待接后端）

**7 步表单**

| 步 | 问题 | 控件 | 校验 |
| --- | --- | --- | --- |
| 1 | 是哪只宠物不舒服？ | 宠物大卡 | 必选（默认第一只） |
| 2 | 主要不舒服在哪个部位？ | 8 个部位 chip | 必选；**切换部位会清空已选症状** |
| 3 | 具体有哪些表现？ | 多选（命中危标的显示「高危信号」角标） | 至少 1 项 |
| 4 | 这种情况持续多久了？ | 单选 | 必选 |
| 5 | 目前的精神与进食状态？ | 单选 | 必选 |
| 6 | 还有以下伴随情况吗？ | 多选 | 可跳过 |
| 7 | 还有什么想补充的？ | textarea +「添加患处照片」 | 选填（⬜ 照片为数量模拟） |

8 个部位：头颈五官 / 皮肤被毛 / 消化系统 / 呼吸循环 / 四肢骨骼 / 泌尿系统 / 行为精神 / 其他

**评分算法（`data/triage.js`，与后端约定完全一致）**

```
一票否决：所选症状命中 redFlag（共 8 条）→ level=emergency, score=10，立即短路返回
  高危：张嘴呼吸/喘不上气、舌色发白或发紫、运动后虚脱晕厥、后肢无力无法站立、
       抽搐意识丧失、排尿困难尿不出来、疑似误食异物或毒物、外伤车祸坠落

否则加权累加：
  时长   今天 0 / 2–3 天 1 / 约一周 2 / 超过一周 3
  严重度 轻微 0 / 明显不适 2 / 精神差不吃不喝 4
  症状加重项  便中带血 +2、呼吸急促 +2（其余症状不计分）
  伴随（多条累加）精神萎靡 3、食欲下降 3、发热 2、呕吐 2、腹泻 2、饮水异常 1、睡眠增多 1

分级：score >= 3 → urgent(建议尽快就诊)；否则 home(可先居家观察)
```

**可解释性**：每个加分项都生成一条 `factor`（`{ text, w, danger }`），报告页可展开逐条查看 —— 这是"不黑盒打分"的核心设计。

**操作**：context 建议 actions 按 level 取模板，再按部位追加（皮肤→每日同光线拍照；消化→停零食留排泄物照片；泌尿→记录排尿次数）。

**产出**：末步 `saveReport({type:'ai', ...})` → `replace` 到 `/report/<id>`；若第 3 步出现高危信号，页面顶部即时告警并提供「急诊医生」直达，**但不打断问卷**（注释：「问卷可继续填完，报告可带给医生看」）。

⚠ 无草稿机制，中途退出全部丢失。

---

### 2.9 真人医生问诊

#### 2.9.1 医生列表 `Doctors.vue`（`/doctors`） 🟡

- **科室 chip**（8 项）：全部 / 犬猫内科 `internal` / 外科骨科 `surgery` / 皮肤病 `derma` / 急诊重症 `er` / 异宠专科 `exotic` / 营养体重 `nutrition` / 眼科 `eye`
- 入参 `query.dept`：由 AI 问诊升级、预问诊高危 warning、报告页共同推导（统一 `deptOf()` 映射）
- **排序**：在线优先 → 评分降序 → 响应分钟升序
- 卡片字段：头像首字、姓名 + 职称、在线态、医院、标签、评分、**接诊量**、`¥19 起`（= `min(mode.price)`）、响应时间/排班
- **AI 病例摘要卡**：读 `sessionStorage`，标题「AI 已为 X 生成初步判断」，可展开看宠物/症状/主诉/AI 判断
- 空态：「该科室暂无在线医生，试试切换科室或取消「仅看在线」。」

#### 2.9.2 医生详情 `DoctorDetail.vue`（`/doctor/:id`） 🟡

- hero（姓名/职称/医院 + 评分·接诊量·执业年三宫格）、排班条、擅长领域、资质认证、**AI 病例摘要区**（有摘要则可补充说明 textarea，无摘要则手填）、**问诊方式三选一**、用户评价列表
- **问诊方式与价格**：

| id | 方式 | 价格 | 说明 |
| --- | --- | --- | --- |
| `text` | 图文问诊 | **¥19** | 上传照片与描述，24h 内回复，可追问 3 次 |
| `voice` | 电话问诊 | **¥39** | 预约时段后医生致电，15 分钟通话 |
| `video` | 视频问诊 | **¥59** | 面对面看诊，20 分钟通话 |

- 底部提示：「问诊费用用于医生诊疗服务，接诊前可随时取消并全额退款。」
- 提交 → `createConsultOrder()` → `replace` 到 `/consultation/<orderId>`；Toast「已提交给 X 医生，请稍候」

#### 2.9.3 问诊室 `ConsultationRoom.vue`（`/consultation/:id`） 🟡

**消息类型**：`system`（居中胶囊）/ `text`（`from: me|doc`）/ `rx`（处方卡，含 `drugs[{name,dose,use}]` + `note`）

**脚本化接诊时序**

```
进入（messages 为空时）
  → 系统条「已向 X 医生提交问诊单，N 分钟内接诊」
  → 1500ms 后医生第一轮：「你好，我是X医生。已看过 AI 的初步判断和病例摘要，不用重复描述。」
  → 用户每发一条 → 1200ms typing → 下一条脚本
  → 第 2 轮之后再延时 900ms → 推送【处方卡】
      耳道清洁液 / 复方制霉菌素软膏 + 用药与复查建议
  → 每次回复后 state 置 'replied'
```

**会话状态条**：`pending`「已提交，等待医生接诊」/ `replied`「医生已回复，可继续追问」/ `closed`「本次问诊已结束」

**电话/视频**：非图文时在消息流上方渲染通话卡（视频→「发起视频」/ 电话→「呼叫」）；⬜ `startCall()` 仅 Toast「演示环境暂不支持真实通话，已通知医生改以图文继续」

**持久化**：消息写进订单对象落在 `petwise_consult_orders`；⚠ `state='replied'` **只改内存对象**，刷新后回到 `pending`（消息仍在，脚本不重播）。

#### 2.9.4 评价 `ConsultationRoom.vue`（结束弹层） 🟡

- 5 星（默认 5）+ 多选标签：`['专业','回复及时','有耐心','建议实用','讲得清楚']`
- 提交 → `rateOrder()` 写 `petwise_doctor_ratings` → `closeOrder()` → **立即生成 human 报告** → `replace` 到报告页
- Toast「评价已提交，已生成问诊报告」

---

### 2.10 问诊报告 `Report.vue`（`/report/:id`）

**功能**：把一次问诊固化为可带走、可执行的结构化产物。 🟡

**两种来源，同一套结构**

| 类型 | 徽标 | 生成方 |
| --- | --- | --- |
| `ai` 预问诊报告 | sparkle | 预问诊末步 `scoreTriage` 产出 |
| `human` 真人问诊报告 | stethoscope | 问诊室结束评价时固化（含 `doctor` / `doctorAdvice` / `rx`） |

**报告结构**

```
id 'rp'+ts / createdAt / date / archived / reminded / type / orderId
petId / petName / title / preview / reportNo（编号 PR-xxxx）
chief: { partLabel, symptomLabels[], durationLabel, severityLabel, accompanyLabels[], note, photos,
        records?[{kind,label,value,date,note}] }   ← 预问诊「从档案导入」勾选的近期变化
triage: { level, label, short, advice, causes[], actions[], score, factors[], followUp }
doctor(human): { id, name, title }
doctorAdvice(human): string[]       ← 医生所有文字消息
rx(human): { drugs:[{name,dose,use}], note } | null
```

**页面分区**：封面（品种/年龄/报告编号）→ 主诉（表现/持续/状态/伴随/补充/附件）→ **近期变化时间线**（`chief.records`，来自健康档案导入）→ 分诊结论（复用 `TriageCard`，置信度 = `emergency?'高':'中'`）→ **评分依据**（默认展开，逐条 `factor.text` + `+w`，`danger` 项整行标红并显示「急诊」）→ 医生建议 → 用药方案 → 复查计划 → 免责声明

**底部三个操作（真实副作用）**

| 操作 | 行为 | 幂等 |
| --- | --- | --- |
| **存入档案** | 在 `petwise_pet_records` 追加一条 `kind:'symptom'` 记录，note 模板：`【问诊报告】<症状> — <分级>。<建议>` | ✅ `archived` 置位后置灰 |
| **用药提醒** | ① 有处方 → 生成次日「按处方用药：<药名>」日程；② 必生成复查日程：`home → +3 天「复查：症状是否缓解」`，其它 `→ +7 天「复诊：按医生建议回访」` | ✅ `reminded` 置位后置灰 |
| **转真人医生** | 推导科室后跳 `/doctors?dept=` | — |
| 右上 **导出** | 拼接**纯文本报告全文**（封面/主诉/分诊/评分依据/医生建议/用药/复查/免责）→ `navigator.clipboard.writeText`（`textarea` + `execCommand` 兜底）→ Toast「报告已复制，可粘贴给医生或保存」 | — |

**科室推荐 `deptOf()`**：`level==='emergency' → er`；部位含"皮肤"→`derma`、"四肢"→`surgery`、"头颈"→`eye`；兜底 `internal`。

---

### 2.11 问诊记录 `Records.vue`（`/records`）

**功能**：AI 问诊 / 真人问诊 / 报告三源聚合回看。 🟡

- Tab：全部 / 智能问诊 / 真人医生（带计数）
- **合成顺序固定为 `[...报告, ...我的订单, ...内置历史]`，不按时间排序**；卡片字段：类型图标、标题、日期、摘要、宠物、医生·方式、状态徽标
- 状态文案：`AI → 已完成`；`pending → 待接诊`（黄）；`replied → 医生已回复`（珊瑚）；其它 `→ 已完成`（绿）
- **点击跳转优先级**：有 `reportId` 进报告页，否则有 `orderId` 进问诊室；⚠ AI 内置记录两者皆空 → 点了无反应
- 空态：「还没有这类问诊记录。」
- 底部两个 CTA：「AI 智能问诊」/「找真人医生」+ 结构化问诊引导卡

---

### 2.12 宠物社区 `Community.vue`（`/community`）

**功能**：信息流 + 话题筛选 + 发布（图文/视频/表情包）+ 点赞评论 + 关注/收藏/举报。 🟡（互动部分持久化）

| 能力 | 规则 |
| --- | --- |
| Tab 推荐/关注 | 「关注」流 = 取**奇数下标**的帖子（模拟关注关系，非真实关系） |
| 话题 chip | 再次点击同一话题取消筛选；6 个话题：成长记录 / 健康管理 / 柯基 / 英短 / 换季护理 / 线下撸猫 |
| 加载更多 | push 一条固定内容演示 |
| 发布 | 最多 3 张图；**新增视频选项**（`videos:1` + `videoDuration`，信息流显示时长胶囊）；**表情包栏 12 个 emoji**（发布与评论两处）；发布后强制回到「推荐」+ 清空话题筛选 |
| 点赞 | 本地 `localLiked/localLikes` ±1，带 `like-pop` 缩放动画 |
| 评论 | 评论面板带 emoji 栏；发送后 `post.comments++` |
| 关注 | 卡片「关注」按钮切换态（本地） |
| 更多操作 | 弹层四选：**收藏**（→ `addFavorite` 写 `petwise_favorites` 持久化）/ 分享（Toast）/ 不感兴趣（本地隐藏）/ **举报** |
| 举报 | 6 项理由（广告或垃圾信息 / 辱骂攻击 / 血腥暴力 / 违法违规 / 侵犯权益 / 其他）+ 补充说明 → `reportPost()` 写共享键 `petwise_post_reports` → **管理端「内容审核 → 举报处理」实时可见**（真实双端闭环 ✅） |
| 图片 | 色调色块占位，非真实上传 |

空态：「这个话题下还没有动态，换个看看？」

**接口映射**：`GET /posts` / `POST /posts` / `POST /posts/{id}/like` / `GET|POST /posts/{id}/comments` / `POST /posts/{id}/report` / `POST /favorites`

---

### 2.13 即时消息 `ChatList.vue` / `ChatRoom.vue`

- 会话列表（`/chat`）：头像 + 在线绿点 + 最后一条 + 时间 + **未读红徽标**（mock 合计 2，Dock 上同步显示）+ 类型 pill（`vet 兽医` / `group 群聊` / `friend 好友`）
- **通讯录入口**：列表顶部「通讯录」行（显示联系人总数）+ 头部右上角用户图标 → `/contacts`
- **搜索**：顶部搜索框按昵称/最近消息实时过滤（`visibleConvs`）
- 聊天室（`/chat/:id`）：`HH:mm` 时间戳气泡、发送后 1100ms 对方"正在输入"→自动回复固定文案「收到～ 我看看」
- **表情面板**：composer 区 emoji 按钮 → 面板选表情插入输入框
- **图片消息**：composer 图片按钮 → `sendImage()` 插入随机色调图片气泡，点击「查看大图」预览
- **长按操作**：消息长按 550ms（或右键）→ 菜单：复制 / 删除
- **对方信息卡**：点顶部名字/更多 → 底部弹层：头像 + 身份徽标 + 简介 + **宠物卡** + 社区动态/粉丝统计 + 「查看 TA 的社区」+ 关注切换
- **新会话回退**：`conv` 查找不到会话时回退到 `allContacts`（通讯录联系人），空消息态「打个招呼，开始你们的第一条消息吧」——通讯录里没有历史会话的好友/社群可直接发起聊天
- ⬜ 未实现：WebSocket 实时推送、已读回执（未读数恒不清零）

---

### 2.13b 通讯录 `Contacts.vue`（`/contacts`）

**功能**：按「好友 / 兽医 / 社群」三组浏览全部联系人，搜索直达，点击进入会话或资料页。 🟢

| 区块 | 规则 |
| --- | --- |
| 快捷入口 | 「新的朋友」（徽标 2，点击 Toast 占位）、「AI 养宠助手」→ `/consult/ai` |
| 搜索 | 按姓名 / 简介实时过滤，跨组保留有命中的分组 |
| 我的好友 | 遛弯搭子、阿橘的日常、柯基豆豆；在线绿点 + 类型色调头像（sand） |
| 我的兽医 | 老张（直达会话）+ 陈静/王铮/苏晴（→ `/doctor/:id` 资料页）；**认证兽医**徽标 + coral 色调头像 |
| 宠物社群 | 橘座铲屎团（直达会话）+ 胖柯基联盟、新手互助会；sage 色调头像 + 群聊标签 |
| 跳转规则 | `chatId` → 已有聊天室；`doctorId` → 兽医资料页；都没有 → `/chat/<联系人id>` 发起新会话（聊天室回退查找） |
| 底部统计 | 「N 位联系人 · 点击即可开始对话」 |

数据源：`mock.js` 的 `contactGroups`（三组）与 `allContacts`（扁平，供聊天室回退）。
⬜ 未实现：添加联系人（Toast 占位）、字母索引、联系人持久化。

---

### 2.14 我的 `Profile.vue`（`/profile`）

| 区块 | 内容 |
| --- | --- |
| 用户卡 | 头像 + 昵称 + 脱敏手机（`138****8888`）+ bio + **编辑**（弹层改昵称/bio） |
| 三宫格 | 宠物数 / 粉丝 / 关注 |
| 我的宠物 | 卡片 → `/pet/:id`，右侧显示健康分；⬜「＋ 添加」实际跳到识别页 |
| 功能菜单 | 问诊记录（徽标 5）→ `/records`；**我的钱包**（余额 ¥68.50）；**账号管理**（安全 · 隐私 · 注销）→ `/account`；我的收藏（徽标 4）→ `/favorites`；**我的社区主页**（328 粉丝）；提醒与日程 → `/schedule`；意见反馈 → 面板；关于 → Toast |
| **我的钱包** | 弹层：余额卡 + 充值（30/50/100/200 四档）+ 提现 + 明细列表；`walletTransact()` 写 `petwise_wallet`，`amount>0` 入账 / `<0` 出账，流水只追加 |
| **意见反馈** | 3 类（遇到问题 `bug` / 功能建议 `suggestion` / 其他 `other`，默认 suggestion）+ textarea → 写 `petwise_feedbacks` → **管理端可见**（真实双端闭环 ✅） |
| **清除缓存** | 统计 `petwise_` 前缀键占用字节数 → 一键清除（**保留 `petwise_auth`** 登录态） |
| 退出登录 | 清 `petwise_auth` → `replace('/login')`（防止返回已登录页） |

**我的收藏 `Favorites.vue`**：4 类筛选（全部 / 品种 / 帖子 / 贴士），整行跳转 + 右侧 × 取消收藏。
合并展示 `customFavorites()`（社区收藏写入，持久化）与内置演示收藏；取消自定义收藏真实删除并持久化。

---

### 2.14b 账号管理 `Account.vue`（`/account`）

**功能**：参照微信「账号与安全」+ 抖音「隐私设置」+ Apple 5.1.1(v) 注销要求设计的账号中心。 🟢（偏好/黑名单真实持久化，注销为演示闭环）

| 分组 | 内容 | 规则 |
| --- | --- | --- |
| 账号概览卡 | 头像 + 昵称 + 脱敏手机 + **安全等级徽标**（高/中/低，按绑定数粗评） | |
| 账号与安全 | 手机号（更换）、登录密码（修改）、实名认证（已认证） | **修改密码全站唯一实现在此**（原 Profile 弹层迁入，规则同 §4.1.7）；更换手机号 = 新号 + 6 位验证码，成功后同步 `petwise_auth.phone` |
| 账号绑定 | 微信 / Apple ID 开关 | `saveAccountPrefs({binds})` 写 `petwise_account_prefs` 持久化 |
| 隐私管理 | **个性化推荐**开关、社区动态可见范围（公开/仅关注者/仅自己）、**黑名单管理**、个人信息收集清单 | 个性化推荐关闭项为算法推荐新规要求；黑名单 `petwise_blacklist`（种子 2 人，解除即删）；收集清单按个保法公示 5 类信息与用途 |
| 登录设备管理 | 本机 / iPad / 网页端三条，「下线」按钮 | 演示静态数据 |
| 危险区 | **注销账号**（红色警示，标注冷静期 7 天） | 见下方流程 |

**注销四步流程**（全屏覆盖层，步骤指示「步骤 N / 4」）

1. **条件检查**：账号状态正常 ✓ / 钱包余额已清零（失败显示余额 + 「去处理」跳钱包）/ 无进行中问诊单（失败跳问诊记录）+ 用户勾选「重要数据已备份」；条件不满足时「下一步」禁用
2. **风险明示**：红色卡片列出 6 类将被永久删除的数据（档案/问诊/社区/收藏/钱包/账号本身）+ 注销原因 6 选 1 + 勾选「我已了解上述风险」
3. **身份验证**：向当前手机号发送 6 位验证码（`CodeInput` 组件，60s 冷却 + 每日 5 次频控共享键），附冷静期规则提示
4. **冷静期页**：「注销申请已提交，账号将于 7 天后（动态日期）永久注销」+ 规则卡；两个终态动作——**撤销申请**（恢复账号）/ **退出并清除本机数据**（`clearLocalAccountData()` 清空全部 `petwise_*` 键 + 登出 → `/login`）

> 设计依据：条件前置检查与财产结清（支付宝模式）、60 天级冷静期与「期间登录即撤销」（微信模式）、红色损失明示与替代方案（主流通用）、注销内可见入口（Apple 审核指南 5.1.1(v)）。

**数据层**（`ops.js`）：`accountPrefs()/saveAccountPrefs()`（`petwise_account_prefs`）、`blacklist()/unblockUser()`（`petwise_blacklist`）、`clearLocalAccountData()`；短信频控 `smsSendCount()/bumpSmsSend()/SMS_DAILY_MAX` 与登录页共享同一实现。

---

## 3. 管理端功能（apps/admin）

> Vue 3 + Vite，哈希路由，端口 5174。零 HTTP 调用：**数据是 `data/admin.js` 静态数组 + 少量 localStorage**。

### 3.1 登录与布局 🟡

- 登录：`admin / petwise` 字符串比对 → `localStorage['petwise_admin_auth'] = '1'`；失败提示「账号或密码不正确（演示：admin / petwise）」
- 守卫：非登录页且标记非 `'1'` → 跳登录；已登录访问登录页 → 跳看板（**无 token、无过期、无角色**）
- 侧栏菜单 8 项，徽标：内容审核硬编码 `2`；用户反馈取真实 `open` 计数
- 顶栏面包屑 + `route.meta.title`；⬜ 搜索框无 `v-model`，不可搜索；环境标签「CV + LLM 服务正常」为**硬编码文案，不探测服务**
- 退出清标记 → 跳登录

### 3.2 数据看板 `Dashboard.vue` 🟡（指标真实化）

- 4 张指标卡**读共享键做真实增量**：注册用户 = 12,840 + 内置 + `petwise_admin_users`；累计识别 = 42,130 + `petwise_recognitions`；累计问诊、在档宠物同理
- **运营待办四项真实计数**：待处理举报（`petwise_post_reports` pending）/ 待审核内容（posts pending）/ 识别纠正待审（内置 + App 端 review）/ 转人工问诊，点击跳转对应页
- **系统状态卡**：`modelStatus` 真实模型配置（狗 `convnext_large`·130 类、猫 `efficientnet_v2_l`·60 类，均 cb_focal 长尾均衡 @384）+ API 网关 + 数据回流链路 + live 脉冲点
- **今日动态 feed**：`latestRecognitions` / `latestReports` 取共享键最新记录
- 保留手写 SVG 双折线图（识别·珊瑚 / 问诊·松绿）与品种分布进度条
- ⬜ 无时间范围切换、无导出

### 3.3 用户管理 `Users.vue` 🟡（增删查改 + 兽医双 Tab）

- **双 Tab**：普通用户 / 兽医账号（各带真实计数）
- 用户表列：用户 / 手机号 / 宠物数 / 注册时间 / **来源**（App 注册 / 管理端新增）/ 状态 / 操作
- 搜索匹配姓名或手机号；筛选 全部 / 正常 / 已冻结
- **宠物数不看 `u.pets` 字段**，而是 `pets.filter(p => p.owner === u.name).length`
- **新增用户**：弹层表单（昵称 ≥2 字、手机号正则校验 + 全表查重、初始密码 ≥6 位、宠物数 0–20）→ `unshift` 写 `petwise_admin_users`（**持久化，看板计数联动**）
- **抽屉详情**：账号状态卡（含来源徽标）+ 名下宠物卡 + 治理操作
- **治理操作全部真实**：冻结/恢复（自定义用户写回持久化）、**重置密码**（生成 6 位随机密码，弹层展示 + 复制）、导出数据（Toast 演示）、**删除账号**（仅管理端新增账号可删；演示内置账号提示不可删）
- **兽医 Tab**：卡片网格（头像 / 科室·医院 / 在线徽标 / 电话 / 累计问诊 / 评分 / 入驻日期）+ 搜索（姓名/医院/科室）+ 筛选（全部科室 / 在线接诊 / 已冻结）+ 操作（上下线切换、冻结/恢复、删除——内置兽医同样受保护）
- 新增兽医写 `petwise_admin_doctors`；冻结自动下线

### 3.4 识别记录 `Records.vue` ✅（识别审核 + 数据回流）

- 数据源：静态演示数据 + App 端写入的 `petwise_recognitions`（双端共享键，同源时实时可见）
- 列：编号 / 用户 / 识别结果 / **纠正来源**（模型预测「X」）/ 置信度 / 时间 / 状态 / 操作
- 置信度分级：`>=0.85 good`、`>=0.60 mid`、`<0.60 low`（低于 0.60 自动标记「低置信待审」）
- 筛选 tab：全部 / **纠正待审核**（真实计数）/ 已采纳
- **审核操作**：`通过` → `approved`（Toast「已通过，计入训练数据集」，同步写回共享键，App 端徽标变「已采纳」）；`驳回` → `rejected`（展示回模型原预测）
- **导出训练数据集**：一键导出全部 `approved` 样本为 JSON（`image_ref` + `species` + `label` 人工标签 + `model_predicted` + `model_confidence`），按周导出后在 `cv/` 增量训练——「用户纠正 → 审核 → 数据回流」闭环的管理端落地
- ⬜ 无排序/分页/详情页；审核动作目前只改共享键与内存

### 3.5 内容审核 `Moderation.vue` 🟡（AI 预审 + 举报处理双 Tab）

- **双 Tab**：内容审核（静态 posts）/ 举报处理（App 端真实举报）
- **内容审核**：筛选 全部 / 待审核 / 已通过 / 已驳回；待审卡片文本标红
- **AI 预审行**（每条内容下方实时渲染）：用 `sensitiveWords` 词库扫描正文 → 命中则列出命中词 chips + 归类（广告导流 / 辱骂攻击 / 违法违规）+「建议驳回」；未命中显示「未命中风险词库，内容未见异常，建议通过」——**不再是硬编码文案**（修复了与 Settings 词库无联动的问题）
- 人工操作：`通过` → `pass`；`驳回` → `reject`（Toast + 状态徽标 + 「已放行至社区 / 已下架并通知作者」备注）
- **举报处理**：读共享键 `petwise_post_reports`（App 社区举报实时同键）；卡片展示被举报动态 ID、举报理由 chip、补充说明、举报人、时间、状态徽标
- 处理动作：**下架内容** → `state='removed'`；**驳回举报** → `state='ignored'`；**写回 localStorage**，看板「待处理举报」计数同步下降（真实闭环）
- 筛选：待处理（真实计数）/ 全部记录；空态引导「App 端用户提交的举报会实时出现在这里」

### 3.6 问诊记录 `Consults.vue` 🟡

表格：编号 / 用户 / 宠物 / 问诊主题 / 对话轮次 / **模型标签（GLM-4V / GLM-4）** / 时间 / 状态（已转人工 / 已完成）。
⬜ 无会话回放、无转人工跟进、无导出。

### 3.7 公告管理 `Announce.vue` ✅（真实双端闭环）

| 字段 | 控件 | 约束 |
| --- | --- | --- |
| 标题 | input「一句话说清这条公告」 | 必填（禁保存） |
| 类型 | select | `event 活动` / `info 通知` / `warn 提醒` |
| 正文 | textarea（将在 App 首页展示） | 必填 |

- 新建：`unshift({id:'a'+Date.now(), title, body, level, date, active:true})` → 持久化 → Toast「公告已发布，App 首页将同步展示」
- 行操作：上线/下线（`active` 取反）、删除；🟡 编辑分支代码存在但**列表无入口**（不可达）
- 移动端效果：`Home.vue` 只展示 `active===true` 且未被用户收起的公告

### 3.8 用户反馈 `Feedback.vue` ✅（真实双端闭环）

- 来源：App「我的 → 意见反馈」写入的 `petwise_feedbacks`
- 类型标签 `bug 问题 / suggestion 建议 / other 其他`；筛选 全部 / 待处理（真实计数）/ 已处理
- 唯一操作「标记已处理」→ `state='resolved'` → Toast；侧栏徽标同步减少
- ⬜ 无回复用户、无删除、无重新打开

### 3.9 系统设置 `Settings.vue` 🟡

| 区块 | 字段 | 默认值 |
| --- | --- | --- |
| 模型与服务 | 置信度阈值 | `0.6`（可 0.5/0.6/0.7） |
|  | LLM 选择 | `GLM-4V（图文）` / `GLM-4（纯文本）` |
|  | 医疗免责声明开关 | `true` |
|  | 新用户注册开关 | `true` |
| 敏感词库 | 增删词条 | 默认 `['加微信','低价药','代刷','私聊转账']` |
| 管理员与角色 | 静态表格（超级管理员 / 内容审核员 / 运营专员） | ⬜ 不可编辑 |

> ⚠ **重要**：`petwise_admin_cfg` 与 `petwise_admin_words` 目前**只有 Settings 页自己读写，没有任何业务侧消费方**——所谓"保存后即时生效"实际只对下一次打开 Settings 生效（既不影响 `vision` 阈值，也不参与 `Moderation` 审核）。详见 [§7](#7-已知限制与占位清单)。

### 3.10 双端数据共享契约

两个 App 使用**同名同构**的 localStorage 键，因此在同一浏览器里天然闭环：

| 键 | 结构 | 管理端 | 移动端 |
| --- | --- | --- | --- |
| `petwise_announcements` | `{id,title,body,date,level,active}[]` | ✅ 读写 | ✅ 只读（过滤 active + 未收起） |
| `petwise_feedbacks` | `{id,user,type,text,time,state}[]` | ✅ 读 + 改 state | ✅ 写入 `state:'open'` |
| `petwise_recognitions` | `{id,species,predicted,corrected,confidence,alternatives,status,imageRef,time}[]` | ✅ 审核（通过/驳回）+ 导出数据集 | ✅ 写入识别记录、提交手动纠正 |
| `petwise_post_reports` | `{id,postId,author,reason,detail,reporter,time,state}[]` | ✅ 举报处理（下架/驳回，写回 state） | ✅ 社区举报写入 `state:'pending'` |
| `petwise_ann_dismissed` | `string[]` | — | ✅ 用户"收起公告" |

> `petwise_recognitions` 是「用户纠正 → 管理端审核 → 导出训练集」闭环的载体；
> `petwise_post_reports` 是「用户举报 → 管理端处理 → 看板待办下降」闭环的载体（同源浏览器内实时互通；接后端后由 §4.7 / §4.14.7 / §4.18 接口替代）。

**管理端私有键**：`petwise_admin_auth`、`petwise_admin_cfg`、`petwise_admin_words`、
`petwise_admin_users`（管理端新增用户，看板注册用户计数消费）、`petwise_admin_doctors`（管理端新增兽医）。

**移动端私有键**：`petwise_memos`（备忘录）、`petwise_wallet`（余额 + 流水）、
`petwise_favorites`（社区收藏）、`petwise_sms_sent`（验证码按日频控计数）。

---

## 4. AI 能力：品种识别与问诊智能体

### 4.1 离线训练 `cv/`

**路线**：两个独立模型 + 物种路由（狗/猫视觉差异大，共用一套分类头会互相拉低上限；`kind=auto` 路由成本极低）。

**目录约定**（新增物种零改内核）

```
cv/common/                共享内核：数据增强/归一化/标签/采样器/模型工厂/训练器/评测/导出
cv/<kind>/src/data/dataset.py   build_loaders(root, …) -> (train, val, test, classes)
cv/<kind>/src/data/labels.py    make_labels(...) + CN_JSON
cv/scripts/{prepare,train,export}.sh <kind>
```

**三条命令**

```bash
cd cv
bash scripts/prepare.sh dog    # 切分测试集 + 生成 labels-dog.json
bash scripts/train.sh   dog    # 训练 → artifacts/best-dog.pt
bash scripts/export.sh  dog    # 导出 → artifacts/model-dog-v1.onnx + 注册 manifest.json
# 等价于：python -m common.train.run --kind dog
```

**数据集现状**

| 物种 | 结构 | 规模 | 说明 |
| --- | --- | --- | --- |
| dog | THU-Dogs，lst 清单 + 双 bbox（head/body） | 130 类；train 65228，val/test 各 2600 | 官方无测试集，由 `prepare.sh` 按每类确定性切分（固定 seed、幂等） |
| cat | `ImageFolder`（自带 train/val/test） | 60 类；44794 / 12784 / 6458 | 无需再切分 |

**已在代码里落地的准确率手段**

| 手段 | 作用 | 默认 |
| --- | --- | --- |
| bbox 概率裁剪 | 训练时按概率裁 body 框，验证/测试强制整图 —— **对齐线上推理分布**，避免离线虚高上线掉点 | 训练 0.5 / 评测 0.0 |
| 类平衡采样 | 按类频 `-alpha` 次幂加权 | `alpha=0.5`（1.0 会过拟合） |
| 冻结预热 + warmup + 余弦退火 | 先冻骨干若干轮，再解冻 | `freeze_epochs` / `warmup_epochs` 可配 |
| EMA | 验证与保存均用 EMA 权重 | 开启 |
| 增强套餐 | RandomResizedCrop(0.6~1.0) + RandomAffine + ColorJitter + RandomErasing | 开启 |
| Mixup / CutMix | 进一步提升泛化 | 可配 |
| TTA + macroRecall | 评测指标更贴近长尾 | 开启 |
| 评测预处理严格对齐线上 | `Resize(BICUBIC) + CenterCrop` == 线上 `ImageOps.fit` | ✅ |

**交付契约**：`export.sh` 产出 `model-<kind>-vN.onnx`（输入 `input` / 输出 `logits`，动态 batch）+ `labels-<kind>.json`（**下标即类 id**）+ 累积写入 `manifest.json`。

### 4.2 在线推理 `services/vision`

**端点**（仅两个，全部经 `X-Internal-Token` 鉴权）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 返回 `{status:'ok'\|'degraded', models:[], provider, env}` |
| POST | `/internal/v1/recognize` | multipart：`image`(≤10MB) / `kind`(dog\|cat\|skin\|auto) / `topK`(1–10，默认 3) |

**模型注册（`manifest.json` 版本契约）**

```json
{ "models": [
  { "kind": "cat", "version": "v3", "onnx": "cat-v3.onnx", "labels": "cat-labels.json",
    "imageSize": 224, "mean": [0.485,0.456,0.406], "std": [0.229,0.224,0.225] },
  { "kind": "dog", "version": "v2", "onnx": "dog-v2.onnx", "labels": "dog-labels.json" }
]}
```

缺 `imageSize/mean/std` 时回落到 ImageNet 常量；同名 kind 后者覆盖。

**推理链路**

```
load_image  → EXIF 校正 + RGB + 大小校验
to_tensor   → ImageOps.fit(BICUBIC) → /255 → 归一化 → NCHW
session.run → logits →（若和不为 1 则自动 softmax 兜底）
top_k       → argpartition 取 top-k，按概率降序
判拒识      → best < REJECT_THRESHOLD(0.5) → 返回「未识别到犬种」+ isUnknown=true（仍保留 candidates）
分级        → ≥0.85 good / ≥0.45 watch / 否则 risk
```

**关键设计**

| 设计 | 说明 |
| --- | --- |
| **拒识优先于分级** | 模型只训练了犬/猫品种，没有"非宠物"负样本；低置信多为非宠物或模糊图，强行给品种会摧毁可信度。因此先拒识，再谈分级 → `risk` 实际只存在于 `[0.45, 0.5)` 窄带 |
| **多模型路由 `kind=auto`** | 各模型各跑一次，取 top-1 置信最高者；单模型时退化为该模型；某模型不可用则跳过 |
| **会话缓存** | 按 `kind:version` 缓存 ONNX Session，换版本自动新建 |
| **启动预热** | 用 128 灰图跑一次前向，避免首个真实请求承担模型加载开销 |
| **无 TTA** | 单次前向，把延迟留给网关 3s 超时预算 |
| **缺权重不算致命** | 启动时无 manifest → 服务照常起来，`/health` 返回 degraded，识别返回 503，由 api 降级 |

**返回字段**

| 字段 | 说明 |
| --- | --- |
| `id` | `r_xxxxxxxx`，由 api 落库后回填 |
| `title` / `sci` / `species` / `breedId` | 拒识时分别为 `未识别到犬种` / `""` / `unknown` / `unknown` |
| `confidence` | top-1（round 4） |
| `metrics[]` | 正常 4 项（品种匹配动态 + 体态/被毛/眼鼻三项静态占位）；拒识或低置信时仅 1 项 |
| `note` | 结论说明；拒识时给"可能是非犬宠物/角度光线不佳，建议拍清晰正面照重试" |
| `candidates[]` | top-k 候选，供前端展示"最接近的品种" |
| `isUnknown` / `modelVersion` | 拒识标记 / manifest 版本号（非契约扩展） |

**错误码**：`60001` 模型未就绪(503) · `10001` kind 无对应模型(400) · `10002` 图片过大或无法解析(400) · `20003` 内部凭证无效(401)

> ⏳ **当前状态**：`services/vision/artifacts/` 下暂无 `manifest.json` 与 `.onnx`，服务处于 `degraded`，识别恒返回 503。跑完 `cv` 三步-scripts 把产物挂进去即可恢复。

### 4.3 问诊智能体 `services/agent`

**对外能力**

| 端点 | 说明 |
| --- | --- |
| `POST /internal/v1/triage` | 一次性分诊，返回 `TriageResult` + `traceId` |
| `POST /internal/v1/triage/stream` | SSE 流式分诊（6 个阶段进度帧 + done 帧） |
| `POST /internal/v1/report/stream` | 问诊报告流式生成 |
| `/internal/v1/knowledge/{stats,search,ingest}` | 知识库运维接口 |

**图拓扑（6 节点线性流水线，节点失败只记录不中断）**

```
precheck ─▶ retrieve ─▶ gather ─▶ reason ─▶ critique ─▶ finalize
  规则打分    知识检索    工具运行    LLM推理    合规自检     组装契约
```

| 节点 | 职责 | 关键行为 |
| --- | --- | --- |
| `precheck` | 危险信号识别 + 加权评分 | 产出 `factors`（逐项可解释）与 `baseline_level` |
| `retrieve` | 知识库混合检索 | 异常一律降级返回空列表，**绝不中断链路** |
| `gather` | 运行三个工具 | `pet_profile`（读档案摘要）/ `schedule_suggestion`（按关键词给随访提醒）/ `prescription_guard` |
| `reason` | LLM 生成 JSON 草稿 | 角色边界写死在 system prompt：面向宠主、禁处方、只能用给定事实；**规则更严时覆盖模型**（规则判 emergency 而模型没判 → 强制修正并记录 warning） |
| `critique` | 合规自检 | 检查 `advice`：命中处方或过度承诺 → 打码为「【请遵医嘱】」；必要时让 LLM 重写一次 |
| `finalize` | 组装契约 | **红旗在此二次兜底**：有 `red_flags` 强制 `emergency`；`advice` 强制拼接免责声明；`factors` 截断 8 条、`sources` 5 条、`causes/actions` 各 4 条 |

**护栏三条硬规则**：① 危险信号一票否决 ② 禁止处方 ③ 免责声明必带。

- RED_FLAGS 16 条（呼吸困难/张口呼吸/抽搐/昏迷/休克/大量出血/无法排尿/尿不出来/误食/呕吐不止/难产/中毒/骨折/眼球突出/流产/腹部膨大）权重 3–4
- 症状权重 18 条（拒食 2、便血 3、血尿 3、跛行 2…）；时长今天 0 → 超过一周 3；严重度 0/1/3
- **分级**：`has_danger || score>=7 → emergency`；`score>=3 → urgent`；否则 `home`
- 处方正则涵盖剂量表述与常见处方药名/商品名（阿莫西林、头孢、多西环素、恩诺沙星、泼尼松、伊维菌素、速诺、大宠爱…）；过度承诺正则：`肯定没事 / 保证 / 无需就医`

**知识库 RAG 链路**

```
灌库：语料目录(.md/.json/.jsonl/.csv/.tsv) → loaders(含 front-matter) → 按标题切块
      → 段落合并 + 滑窗(380/60) → embedding → kb_chunk(pgvector)
检索：query → embedding → 向量粗召回(30) ┐
                        → 关键词召回(20) ┴→ 混合打分 0.7*sim + 0.3*kw_norm
                        → 重排 → 阈值(0.30)过滤 → 同文档限 2 段 → top 6
```

| 可插拔点 | 选项 | 默认 |
| --- | --- | --- |
| Embedding | `hash`（blake2b 哈希，零依赖，禁用于效果评测）/ `local`（sentence-transformers）/ `openai` | `hash` |
| 重排 | `heuristic`（标题命中 +0.15、短语命中 +0.10、覆盖度 ×0.08、长段 −0.03、source 加成 first_aid 0.06→breed 0）/ `cross-encoder` | `heuristic` |
| LLM | 任意 OpenAI 兼容端点 | `gpt-4o-mini`（未配 key 走 mock） |

**存储与索引**：`kb_document` + `kb_chunk`（`Vector(768)`，未装 pgvector 时降级为 NullType）；`schema.sql` 建 HNSW（`m=16, ef_construction=64`）、pg_trgm GIN、`(source_type, species)` 复合索引；CLI 支持 `init-db / ingest / search / stats / reset`。

**架构选型说明**： LangGraph 是**可选 extras**，当前实际执行器是 `run_agent` 的线性循环（`engine_name()` 返回 `sequential`）；`build_graph()` 已定义（为将来接入条件边/回环预留），但未被调用。因此**当前是单智能体 + self-critique，不是多智能体**。

**记忆**：Redis（优先，失败降级内存）保存最近 6 轮会话，TTL 1800s；⚠ 目前只由 `/triage/stream` 写入，**尚无任何节点读取**。

**Mock 模式（默认）**：`LLM_API_KEY` 为空 → `mock_mode=true` → `reason` 回退规则基线 `_rule_based_draft`，`modelVersion="rules-baseline"`，`used_llm=false`。设置密钥后自动切到真实 LLM，链路代码零改动。

### 4.4 网关调用契约与降级 `services/api/app/clients/`

| 下游 | 超时 | 重试 | 说明 |
| --- | --- | --- | --- |
| vision `/internal/v1/recognize`（multipart） | **3.0s** | 0 | 独立通道，不享受 JSON 通道的 5xx 重试 —— 识别是可降级能力，宁快勿重 |
| vision `/health` | 3.0s | 1 | 抖动值得重试一次 |
| agent 一次性 `triage` | 30.0s | **0** | 注释明确：LLM 不适合自动重试，会烧双倍 Token |
| agent SSE（`triage/stream`、`report/stream`） | **90.0s** | 0 | 覆盖构造时的 30s |

**错误翻译**：`超时 → 60002 "{service} 响应超时"`；`连接失败/≥400 → 60001 "{service} 服务暂不可用"`；`agent 429 → 41001 "今日 AI 问诊额度已用尽，建议转诊真人医生"`。所有请求自动附带 `X-Trace-Id`（ContextVar 串联跨服务日志）。

**降级矩阵**

| 场景 | 行为 |
| --- | --- |
| vision 不可用 | `try_recognize()` 吞掉一切异常返回 `None` → 上层兜底，**主链路绝不失败** |
| agent 不可用 | 抛 `AppError`，由全局异常处理器转契约信封（不静默，因为分诊结果不可伪造） |
| 就绪探针 `/health/ready` | 并行 ping 两个下游，任一不可用 → `status: degraded` 但仍返回 200（"降级继续提供服务，而不是整体下线"） |
| 三服务启动 | 无权重 / 无数据库 / 无 LLM 密钥都能启动，各自降级 |

---

## 5. 横切能力

### 5.1 鉴权与访问控制

| 层 | 现状 |
| --- | --- |
| C 端 | 🟡 `petwise_auth` 存在即视为登录（无 token/有效期）；路由守卫 `meta.public` 放行 splash/login |
| 管理端 | 🟡 `petwise_admin_auth === '1'`（无 token/角色/过期） |
| 服务间 | ✅ `X-Internal-Token` + `hmac.compare_digest` 常量时间比较，失败 401/`20003` |
| 前端请求层 | ✅ 已实现 Bearer 注入 + `code=20002` 静默 refresh 重试一次（⏳未启用） |

### 5.2 AI 配额 ✅

- 每日免费 **3 次**（`AI_DAILY_FREE=3`），存 `{date, used}`，**跨天自动重置**
- 展示：AI 问诊页额度条、问诊中枢、首页快捷入口副标
- 扣除时机：AI 回复生成**之后**（服务��在 `POST /consult/triage` 内部扣减）
- 超限表现：Toast「今日 AI 免费次数已用完，可转真人医生继续问诊」+ **直接跳医生列表** —— 设计意图是"引导转真人而非拒绝服务"
- 免费范围外的能力：上传照片、结构化预问诊、真人问诊均不计额度

### 5.3 免责与合规

| 位置 | 文案 |
| --- | --- |
| AI 问诊页底部 | 「AI 建议仅供参考，不能替代执业兽医的当面诊断。紧急情况请立即就医。」 |
| 报告页底部 | 「本报告由 AI 结合结构化问诊生成，并经由执业兽医确认（human 时），仅供参考…」 |
| agent `finalize` | 强制 `with_disclaimer(advice)`，**模型无法省略** |
| agent `critique` | 处方表述替换为「【请遵医嘱】」并追加「具体用药需要由执业兽医面诊后开具。」 |
| agent `build_report` | 合规不通过时，recommendations 全部替换为「具体方案由执业兽医面诊后给出」 |

### 5.4 可观测性

- `X-Trace-Id` 贯穿 mobile → api → vision/agent，日志可通过 traceId 串联一次请求
- api 侧中间件：`TraceIdMiddleware`（最外层）→ `SlowRequestMiddleware`（慢请求告警）→ CORS
- `/health`（存活，无 IO）与 `/health/ready`（就绪，含下游依赖状态）分离
- agent 侧每次分诊日志：`分诊完成 level=%s used_llm=%s Nms`；vision 侧：`识别 <品种> kind=%s conf=%.3f Nms`

### 5.5 设计系统（C 端）

平静界面 + 低饱和大地色：暖纸白底 + 深松绿墨 + 珊瑚仅作强调色；分层靠发丝描边（`rgba(27,42,34,.07)`）而非重阴影；圆角 4 档 10/14/20/28 + pill；按压统一 `scale(0.978)` / 150–300ms；支持 `prefers-reduced-motion`。

---

## 6. 功能 → 代码 → 接口 速查表

### 6.1 C 端

| 功能 | 页面 | 数据源 | 最终接口（已封装未接线） |
| --- | --- | --- | --- |
| 登录 | `views/Login.vue` | `ops.login` | `authApi.sendCode` / `login` / `me` |
| 首页 | `views/Home.vue` | `mock` + `ops.activeAnnouncements` | `homeApi.summary` / `petsApi.list` / `trend` / `reminders` / `contentApi.announcements` |
| 识别 | `views/Recognize.vue` | `mock.recognitionSamples` | `recognitionApi.recognize` / `history` |
| 品种百科 | `views/BreedDetail.vue` | `mock.breedLibrary` | `contentApi.breeds` / `breed` |
| 宠物档案 | `views/PetProfile.vue` | `mock` + `ops.customRecords` | `petsApi.detail` / `weights` / `records` |
| 日程 | `views/Schedule.vue` | `mock.petSchedule` + `ops` | `scheduleApi.list` / `types` / `create` / `toggleDone` |
| AI 问诊 | `views/Consult.vue` | 本地规则 + `ops.aiQuota` | `consultApi.triage` / `quota` / `case-summary` |
| 预问诊 | `views/PreConsult.vue` | `data/triage.js` | `consultApi.dictionary` / `pre-consult` |
| 医生 | `views/Doctors.vue`、`DoctorDetail.vue` | `mock.doctors` | `consultApi.departments` / `doctors` / `doctor` / `createOrder` |
| 问诊室 | `views/ConsultationRoom.vue` | `ops.consultOrders` | `consultApi.messages` / `sendMessage` / `call` / `read` |
| 评价 | 同上弹层 | `ops.rateOrder` | `consultApi.rate` |
| 报告 | `views/Report.vue` | `ops.reports` | `consultApi.reports` / `report` / `archive` / `remind` / `exportReport` |
| 问诊记录 | `views/Records.vue` | 三源合并 | `consultApi.orders` / `reports` |
| 社区 | `views/Community.vue` | `mock.feed` | `communityApi.posts` / `publish` / `like` / `comments` / `comment` |
| 消息 | `views/ChatList.vue`、`ChatRoom.vue` | `mock.conversations` | `imApi.conversations` / `messages` / `send` / `read` |
| 收藏 | `views/Favorites.vue` | `mock.favorites` | `contentApi.favorites` / `removeFavorite` |
| 我的/反馈 | `views/Profile.vue` | `ops.submitFeedback` | `authApi.me` / `logout`、`contentApi.submitFeedback` |

### 6.2 管理端

| 功能 | 页面 | 数据源 | 闭环 |
| --- | --- | --- | --- |
| 看板 | `views/Dashboard.vue` | `data/admin.js` 静态 | ⬜ |
| 用户 | `views/Users.vue` | 静态 + 内存改动 | ⬜ |
| 识别记录 | `views/Records.vue` | 静态 | ⬜ |
| 内容审核 | `views/Moderation.vue` | 静态 + 内存改动 | ⬜ |
| 问诊记录 | `views/Consults.vue` | 静态 | ⬜ |
| 公告 | `views/Announce.vue` | `petwise_announcements` | ✅ 双端 |
| 反馈 | `views/Feedback.vue` | `petwise_feedbacks` | ✅ 双端 |
| 设置 | `views/Settings.vue` | `petwise_admin_cfg` / `_words` | ⚠ 自读自写，无消费方 |

### 6.3 后端服务

| 能力 | 代码位置 | 关键配置 |
| --- | --- | --- |
| 视觉推理 | `services/vision/app/{registry,engine,preprocess,postprocess}.py` | `REJECT_THRESHOLD=0.5`、`CONF_HIGH=0.85`、`CONF_LOW=0.45`、`TOP_K=3`、`MAX_IMAGE_MB=10` |
| Agent 链路 | `services/agent/app/graph/{nodes,runner,state}.py` | `RETRIEVAL_TOP_K=6`、`RETRIEVAL_CANDIDATES=30`、`SIMILARITY_THRESHOLD=0.30`、`0.7/0.3`、`MAX_CHUNKS_PER_DOC=2` |
| 知识库 | `services/agent/app/knowledge/*` | `EMBEDDING_DIM=768`、`CHUNK_SIZE=380/60`、`RERANK_STRATEGY=heuristic` |
| 护栏 | `services/agent/app/guardrails.py` | 16 危险信号、`>=7 emergency`、`>=3 urgent`、`PRESCRIPTION_ENABLED=False` |
| 网关调用 | `services/api/app/clients/{vision,agent,base}.py` | `VISION_TIMEOUT=3.0`、`AGENT_TIMEOUT=30.0`、`AGENT_STREAM_TIMEOUT=90.0` |
| CV 训练 | `cv/common/*` + `cv/{dog,cat}/*` | `configs/{dataset,train}.yaml` 共 56 键（审计无死配置） |

---

## 7. 已知限制与占位清单

> 这一节刻意写得直白：知道哪些不是真的，比假装它们能用更有价值。

### 7.1 C 端（apps/mobile）

| # | 限制 | 影响 | 优先级 |
| --- | --- | --- | --- |
| 1 | 全部页面走 `data/mock` + `localStorage`，未调后端 | 换设备数据不同步 | P0（接线即可） |
| 2 | 识别无真实推理，结果按 cursor 轮询 3 条 mock | 演示够用，非真实能力 | P0（接 `recognitionApi.recognize`） |
| 3 | AI 问诊非真流式（1300ms 后一次性插入） | 体感尚可，但失去 SSE 增量优势 | P0（agent 已提供 SSE） |
| 4 | 日程不按日期分组，逾期仅加徽标 | 信息密度不足 | P2 |
| 5 | 刷新即丢：社区发布/评论、聊天消息、本地点赞/关注态（收藏已持久化 `petwise_favorites`，首页日志完成态已持久化） | 演示态可接受 | P1 |
| 6 | 登录仍无真实校验（任意 1[3-9]xxxxxxxxx + 6 位）；验证码频控仅前端本地计数 | 仅演示 | P0（接 JWT + 服务端频控） |
| 7 | `Profile.maskedPhone` 非响应式 | 换号后不刷新 | P2 |
| 8 | `PetProfile` 表单默认日期用 UTC | 东八区 0–8 点差一天 | P1 |
| 9 | `Records` 列表不排序 | 最新记录未必在最前 | P1 |
| 10 | 未读数恒为 2，不会清零 | 误导 | P1 |
| 11 | 视频/电话问诊、注册/找回/微信登录均只有 Toast；报告导出为**复制纯文本**（非文件） | 占位，明确未完成 | P2 |

### 7.2 管理端（apps/admin）

| # | 限制 | 优先级 |
| --- | --- | --- |
| 1 | 零 HTTP 调用，业务数据静态 | P0 |
| 2 | `petwise_admin_cfg`（置信度阈值/LLM 选择/免责开关/注册开关）**无任何消费方** | P1 |
| 3 | AI 预审仅本地词库扫描（已接 `sensitiveWords`），无模型审核/图片鉴黄/申诉复审 | P2 |
| 4 | 用户冻结/恢复、新增用户/兽医已持久化；**社区内容审核（pass/reject）仍只改内存**，刷新失效 | P1 |
| 5 | 公告"编辑"分支无入口；用户「导出数据」仅 Toast（重置密码已真实生成 6 位新密码） | P2 |
| 6 | 全局���索框无 `v-model`；环境状态标语硬编码 | P2 |
| 7 | 无分页/排序/批量/审计日志/角色权限拦截 | P2 |

### 7.3 后端与 AI

| # | 限制 | 影响 | 优先级 |
| --- | --- | --- | --- |
| 1 | `services/vision/artifacts/` 无权重 → 识别恒 503 | 识别功能线上不可用 | P0（跑 cv 训练） |
| 2 | agent 未配 LLM 密钥 → 走规则基线（`used_llm=false`） | 链路可跑，智能程度有限 | P0（配 key 即切真实 LLM） |
| 3 | `gather` 在 `reason` 之前执行 → `schedule_tool` 读不到 `draft.level`（急诊跳过分支空转）、`prescription_guard` 恒空 | 工具层部分失效 | P1（调整节点顺序） |
| 4 | 记忆只写不读（仅 `/triage/stream` 写入，无节点消费） | 多轮上下文未利用 | P1 |
| 5 | `keyword_recall` 构造的 `fragments` 未进 where 子句，实际取前 80 行在 Python 侧匹配 | 大规模语料下效率差 | P1 |
| 6 | 默认 embedding 是 `hash`（零依赖但语义弱） | 检索质量受限 | P1（换 `local`/`openai` 后重建库） |
| 7 | `services/api` 业务 router 尚未补齐（当前只有 health + demo） | 前端无法接线 | P0 |
| 8 | C 端消息枚举（`from: me|doc`）与后端契约（`user|doctor`）不一致 | 接线需映射 | P1 |
| 9 | C 端处方字段 `use` vs 后端 `usage`，且无 `days` | 接线需映射 | P2 |
| 10 | 报告由客户端 `saveReport` 生成，后端方案是服务端生成 | 接线时需二选一 | P1 |

---

## 8. 附录：本地持久化键名全集

### 8.1 C 端（apps/mobile）

| 键 | 结构 | 写入方 |
| --- | --- | --- |
| `petwise_auth` | `{phone, mode, time}` | 登录页 |
| `petwise_announcements` | `{id,title,body,date,level,active}[]` | 管理端（App 只读） |
| `petwise_ann_dismissed` | `string[]` | 首页「不再显示」 |
| `petwise_feedbacks` | `{id,user,type,text,time,state}[]` | 我的 → 意见反馈 |
| `petwise_schedule_done` | `string[]` | 日程勾选/撤销 |
| `petwise_schedule_custom` | `{id,type,title,date,petId,custom}[]` | 日程新建、报告「用药提醒」 |
| `petwise_pet_records` | `{id,petId,kind,date,value,note}[]` | 档案录入、报告「存入档案」 |
| `petwise_recognitions` | `{id,species,predicted,corrected,confidence,alternatives,status,imageRef,time}[]` | 识别页保存记录、手动纠正（管理端审核同一键） |
| `petwise_ai_quota` | `{date, used}` | AI 问诊每轮回复后 |
| `petwise_consult_orders` | `{id,doctorId,mode,petId,summary,price,state,createdAt,messages[]}[]` | 下单、发消息、结束问诊 |
| `petwise_doctor_ratings` | `{[orderId]:{doctorId,score,tags,at}}` | 提交评价 |
| `petwise_consult_reports` | 报告对象数组（结构见 §2.10） | 预问诊末步、结束问诊、归档/提醒置位 |
| `petwise_memos` | `{id,petId,text,pinned,time}[]` | 日程页备忘录（输入即存/置顶/删除） |
| `petwise_favorites` | `{id,kind,...}[]` | 社区「更多 → 收藏」（我的页合并展示） |
| `petwise_wallet` | `{balance, txns:[{id,amount,note,time,balanceAfter}]}` | 我的 → 钱包充提 |
| `petwise_post_reports` | `{id,postId,author,reason,detail,reporter,time,state}[]` | 社区举报（管理端举报处理同一键） |
| `petwise_sms_sent` | `{'2026-10-14': n}` | 验证码发送频控（按日计数，上限 5） |

另有 `sessionStorage['petwise_case_summary']`：AI 转真人的病例摘要通道（跨页一次性传递）。

### 8.2 管理端（apps/admin）

| 键 | 结构 | 写入方 |
| --- | --- | --- |
| `petwise_admin_auth` | `'1'` | 登录 / 退出 |
| `petwise_announcements` | 同 C 端 | 公告管理 |
| `petwise_feedbacks` | 同 C 端 | 反馈处理 |
| `petwise_admin_cfg` | `{confThreshold, llm, disclaimer, register}` | 系统设置（**无消费方**） |
| `petwise_admin_words` | `string[]` | 敏感词库（**Moderation AI 预审已消费**） |
| `petwise_post_reports` | 同 C 端 | 举报处理（下架/驳回写回 state） |
| `petwise_admin_users` | `{id,name,phone,pets,joined,state,custom}[]` | 用户管理新增用户（看板注册计数消费） |
| `petwise_admin_doctors` | `{id,name,dept,hospital,phone,online,consults,rating,state,joined,custom}[]` | 用户管理 → 兽医 Tab 新增 |

### 8.3 已知 ID 冲突风险

订单 `o+ts`、报告 `rp+ts`、健康记录 `r+ts`、日程 `s+ts`、`id: 'a'+ts`（公告）、反馈 `'f'+ts` 全部以毫秒时间戳生成，**同一毫秒内连续操作会产生重复 id**，而查找函数均用 `find`（只命中第一个）。接后端后由服务端发号自然解决。
