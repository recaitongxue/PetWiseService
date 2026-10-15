# PetWise 仓库结构与目录职责规范

> 本文回答两个问题：**每一个文件夹该放什么、有什么用**。配合 `ARCHITECTURE.md`(总体架构与依赖纪律)和 `FEATURE-ROADMAP.md`(功能路线图)一起读。
> 标注图例：✅ 已实现骨架 ｜ 🟡 部分实现 ｜ ⬜ 规划中待建

---

## 0. 为什么这样分(30 秒读)

不是按"角色"(前端/后端/模型/AI)切，而是按**部署单元**切。判定一个模块是否该独立成服务，只看三条铁律：

1. **技术栈是否异构**——CV 要 torch+CUDA，主后端要轻量 FastAPI，放一起镜像会胀到几 GB。
2. **失败会不会拖垮主链路**——视觉服务崩了不该让登录、社区一起挂。
3. **伸缩粒度是否不同**——AI 问诊要随对话量弹性扩，普通 CRUD 不用。

命中越多，越要拆。CV 三条全中 → 必独立；智能体命中两条 → 可独立可合并(本项目选独立，便于答辩演示与单独扩容)；普通业务 CRUD 一条不中 → 留在 `services/api`。

---

## 1. 完整目录树

```
PetWiseService/
├── README.md                   ✅ 仓库入口：一句话定位 + 结构导航 + 快速开始
├── apps/                       ✅ 可独立运行/打包的客户端（部署单元）
│   ├── mobile/                 ✅ C 端 App（Vue3 + Vite + Capacitor）→ 原 app/
│   │   ├── src/                ✅ 前端源码（识别/问诊/社区/档案/日程…）
│   │   ├── public/             ✅ 静态资源（图标/兜底图）
│   │   ├── dist/               ✅ 构建产物（gitignore）
│   │   ├── vite.config.js      ✅ 构建配置（outDir 指向 dist/mobile）
│   │   └── package.json        ✅ 依赖与脚本（name: petwise-mobile）
│   └── admin/                 ✅ 运营后台（Vue3 + Vite）→ 原 admin/
│       └── src/  vite.config.js  package.json   ✅（同 mobile 结构，outDir=dist/admin）
├── services/                   ✅ 后端服务，每个子目录一个部署单元
│   ├── api/                    🟡 业务后端（FastAPI）· 唯一对外网关
│   ├── vision/                 🟡 视觉推理服务（FastAPI + ONNX Runtime）
│   └── agent/                  🟡 问诊智能体服务（FastAPI + LangGraph + 知识库）
├── cv/                         ✅ 离线层：模型训练与导出（不对外端口）→ 原 model/
├── packages/                   ✅ 跨服务共享代码/契约
│   └── contracts/              ✅ 契约单一事实源（前后端都从它生成类型）
├── infra/                      ✅ 部署编排（compose / docker / nginx）
├── scripts/                    ⬜ 跨服务脚本（迁移/种子/运维，当前空，预留）
└── docs/                       ✅ 人读文档（架构/接口/结构/路线图）
```

---

## 2. 一级目录详解

### 2.1 `apps/` —— 客户端产物（部署单元）

**有什么用**：存放所有"跑在用户设备上/打包成独立应用"的前端。每一个子目录都是一个独立 `npm run build` 的产物，拥有独立域名、独立权限模型、独立打包流程。

**该放什么**
- `mobile/`：C 端 App。面向宠物主，含识别、问诊、社区、档案、日程等全功能；通过 Capacitor 打包 iOS/Android。
- `admin/`：运营后台。面向平台运营，含公告、反馈、内容审核、知识库管理后台等。
- 未来新增：`apps/miniprogram/`(微信小程序)、`apps/web/`(PC 官网)——平级放入即可，无需改架构。

**禁止放什么**
- ❌ 不要在这里写后端逻辑或直连数据库。所有数据走 `services/api` 的 HTTP。
- ❌ 不要跨 `mobile`/`admin` 互相 import 源码；共享 UI 应抽成 `packages/ui`(待建)或各自复制。

**现状**：`mobile` 与 `admin` 均已迁移并 `build` 通过。`mobile` 含识别/问诊/社区/档案/日程/收藏/消息等页面与 `mock.js` 演示数据。

---

### 2.2 `services/` —— 后端部署单元

每个子目录是一个**独立进程 + 独立镜像 + 独立端口**，通过 nginx(`infra/nginx`)对外收敛。内部统一三约定：统一响应信封 `{code,message,data,timestamp,traceId}`、统一错误码(见 `API.md` 第 3 章)、内部调用走 `X-Internal-Token`。

#### 2.2.1 `services/api/` —— 业务后端（唯一对外网关）🟡
**有什么用**：所有来自 C 端/管理端的请求的唯一入口。负责鉴权、业务编排、数据持久化、调用 `vision`/`agent` 两个内部服务。

| 子目录 | 职责 | 该放 | 禁止 |
|---|---|---|---|
| `app/core/` ✅ | 横切基础设施 | config / logging / envelope / errors / security / deps | 业务逻辑 |
| `app/api/routers/` 🟡 | HTTP 路由(按 openapi tag 拆) | `auth.py` `pets.py` `consult.py`… | ❌ 直接 import `repos` 或写 SQL |
| `app/api/middleware/` ✅ | 请求中间件 | trace(注入 traceId) / timing(耗时) | 业务判断 |
| `app/clients/` ✅ | 出网客户端 | `vision.py` `agent.py`(内部调用+超时降级) | ❌ 同步阻塞调用 |
| `app/domain/` ⬜ | 领域实体与规则 | Pet / Consult / Order 等业务对象 | 框架依赖 |
| `app/services/` ⬜ | 用例编排(事务边界在此) | 一个用例一个文件 | ❌ 直接返回 HTTP |
| `app/repos/` ⬜ | 数据访问 | SQLAlchemy 仓库 | ❌ 含业务规则 |
| `app/models/` ⬜ | ORM 表模型 | 对应数据库表 | 与 `domain` 混用 |
| `app/schemas/` ✅ | 请求/响应 DTO | 由 openapi 生成 | 放业务逻辑 |
| `app/ws/` ⬜ | WebSocket 推送 | 问诊流式帧(见 `events/frames.yaml`) | 业务逻辑 |
| `app/tasks/` ⬜ | 后台任务 | 定时提醒/报表 | 重 CPU 任务 |

**现状**：`core`、`clients`、`middleware`、`exception_handlers`、`main` 已就位并可启动；`routers/` 目前仅有 `health.py` 与 `demo.py`，**52 个业务接口(11 个 tag)待按 `API.md` 铺开**；`domain/services/repos/models` 为占位空包，等待按 tag 填充；`migrations/` 仅有占位，缺 Alembic 迁移。

#### 2.2.2 `services/vision/` —— 视觉推理服务 🟡
**有什么用**：无状态、常驻、毫秒级响应的图像推理。加载 `cv/artifacts` 导出的 `.onnx` 权重，对外提供拍照识别(物种/品种/皮肤病)、排泄物/呕吐物分析、鼻纹身份等。

| 子目录 | 职责 |
|---|---|
| `app/config.py` ✅ | 权重目录、内部 Token、超时 |
| `app/registry.py` ✅ | 模型注册表(一个 kind 对应一个版本权重) |
| `app/preprocess.py` ✅ | 图像预处理(Resize/归一化/张量) |
| `app/postprocess.py` ✅ | 后处理(softmax/标签映射/置信度) |
| `app/engine.py` ✅ | ONNX 会话单例 + 预热 + 推理 |
| `app/guard.py` ✅ | 内部 Token 校验 + 输入校验 |
| `app/main.py` ✅ | FastAPI 入口 |
| `artifacts/` ✅(gitignore) | 存放 `model-<kind>-<version>.onnx` + `manifest.json` |

**禁止放什么**：❌ 不要引入 torch/training 依赖(那是 `cv/` 的事)；❌ 不要直连业务库。

**现状**：推理骨架完整可跑，但缺真实 `.onnx` 权重(识别接口会降级)，需 `cv/` 训练导出后挂载。

#### 2.2.3 `services/agent/` —— 问诊智能体服务 🟡(重点)
**有什么用**：有状态、长连接、可独立扩容的 AI 问诊编排。核心差异点：**知识库子系统 + 多智能体编排**。

| 子目录 | 职责 | 现状 |
|---|---|---|
| `app/knowledge/` 🟡 | **知识库子系统**：模型/向量库/切分/检索/rerank/灌库CLI/API | ✅ 完整实现(见下) |
| `app/graph/` 🟡 | LangGraph 编排(state/nodes/runner/report) | ✅ 编排完整，真实 LLM 待接 |
| `app/prompts/` ✅ | Jinja 提示词模板(v1: triage/reason/critique/report) | ✅ |
| `app/llm/` ✅ | LLM 客户端(支持真实 API + 本地规则兜底) | ✅ |
| `app/tools/` ⬜ | 工具集(查知识库/查档案/计算器…) | 🟡 仅 base |
| `app/guardrails.py` ✅ | 危险信号/紧急分级 | ✅ |
| `app/memory.py` ✅ | 会话记忆 | ✅ |
| `app/config.py` ✅ | embedding/LLM/PG 配置 | ✅ |
| `knowledge_base/` ✅ | 种子语料(breeds/diseases/care/first-aid/faq) | ✅ 6 篇 |
| `app/main.py` ✅ | FastAPI 入口(`/internal/v1/triage` 等) | ✅ |

**现状**：知识库子系统是本项目已建得最完整的模块——含 SQLAlchemy+pgvector 模型、`schema.sql`、可插拔 embedding、Markdown 切分、混合检索(向量+关键词)+rerank、灌库 CLI、知识库管理 API。分诊链路已冒烟(走规则基线兜底)。

---

### 2.3 `cv/` —— 离线模型研发（不对外端口）✅

**有什么用**：模型从"数据"到"权重"的离线生产线。**唯一产物是 `artifacts/` 下的 `.onnx`**，被 `services/vision` 消费。训练(几小时、torch)与推理(毫秒、onnxruntime)生命周期不同，故与 `vision` 严格分离。

**狗与猫各训一个独立模型**（`kind=dog` / `cat`），线上由 vision 按置信度路由；因此目录按「共享内核 + 每个物种一条自包含流水线」组织：两个数据集结构完全不同（狗：lst 清单 + bbox 标注；猫：ImageFolder 无标注），但模型工厂 / 训练器 / 评测器 / 导出器完全通用。

| 子目录 | 职责 | 该放 | 禁止 |
|---|---|---|---|
| `common/` ✅ | 共享训练内核(dog/cat 复用，未来 skin 直接接入) | `data/norm.py`(归一化常量) `data/transforms.py`(预处理) `models/factory.py` `train/trainer.py` `eval/evaluate.py` `export/to_onnx.py` | 物种专属逻辑 |
| `dog/` ✅ | 狗流水线(THU-Dogs 130 类，带 body 框裁剪) | `src/data/thudogs*.py` `configs/` `scripts/` `tests/` `README.md` | 猫的数据逻辑 |
| `cat/` ✅ | 猫流水线(60 类，ImageFolder 无 bbox) | `src/data/cat*.py` `configs/` `scripts/` `tests/` `README.md` | 狗的数据逻辑 |
| `datasets/` ✅(gitignore) | 原始/处理后数据 | `datasets/dog` `datasets/cat`(原 model/data) | 代码 |
| `artifacts/` ✅(gitignore) | 训练产出(两模型共用，manifest 累积) | `best-dog.pt` `model-dog-v1.onnx` `labels-dog.json` `manifest.json` | — |
| 根目录 `pyproject.toml` / `uv.lock` ✅ | 统一 Python 依赖与锁定版本（`uv sync`） | — | — |

> 命令需在物种目录内执行（`cd cv/dog && bash scripts/train.sh`）：`dog/` 与 `cat/` 的包名同为 `src`，
> 脚本会自动把 `cv/` 加入 `PYTHONPATH`，从而导入共享内核 `common`。

---

### 2.4 `packages/contracts/` —— 契约单一事实源 ✅

**有什么用**：前后端类型同源的唯一依据。**改一处，全栈类型跟着变**，避免"后端改了字段前端不知道"。

| 子目录/文件 | 职责 |
|---|---|
| `openapi.yaml` ✅ | 主契约：11 tag / 52 接口 / 30 schema(原 `docs/openapi.yaml`) |
| `events/frames.yaml` ✅ | WebSocket 推送帧定义(API.md 第 5 章) |
| `codegen/README.md` ✅ | 类型生成说明(datamodel-code-generator → Python；openapi-typescript → TS) |
| `README.md` ✅ | 改契约的完整流程 |

**禁止放什么**：❌ 不要在这里写实现；❌ 业务代码不要 import 此目录(只消费生成的类型)。

---

### 2.5 `infra/` —— 部署编排 ✅

**有什么用**：把上面所有部署单元编排成"一键起全栈"。

| 子目录 | 职责 |
|---|---|
| `compose/compose.yml` ✅ | 生产编排(api+vision+agent+pg+redis+nginx) |
| `compose/compose.dev.yml` ✅ | 开发编排(挂源码热重载) |
| `compose/compose.gpu.yml` ✅ | GPU 编排(vision 走 CUDA) |
| `docker/Dockerfile.api` ✅ | 业务后端镜像 |
| `nginx/conf.d/default.conf` ✅ | 反向代理：按路径收敛到三服务 + 静态托管前端 |

**待补**：`Dockerfile.vision` / `Dockerfile.agent`(目前仅 api 有)。

---

### 2.6 `scripts/` —— 跨服务脚本 ⬜

**有什么用**：跨多个服务的运维动作(数据库迁移、知识库种子灌库、一键部署)。当前为空，**预留**。

**该放什么**：`seed_kb.py`(调 agent 灌库 CLI)、`migrate.sh`(alembic)、`deploy.sh`(compose up)。

---

### 2.7 `docs/` —— 人读文档 ✅

| 文件 | 职责 |
|---|---|
| `ARCHITECTURE.md` ✅ | 总体架构、依赖纪律、部署单元关系 |
| `API.md` ✅ | 接口契约详解(11 tag / 52 接口，人读版) |
| `REPO-STRUCTURE.md` ✅(本文) | 目录职责规范 |
| `FEATURE-ROADMAP.md` ✅ | 功能实现路线图(调研+竞争力) |

---

## 3. 跨目录纪律(必须遵守)

1. **依赖方向单向**：`routers → services → repos → models`；`routers` 不得直接 import `repos`(必须经 `services` 层，事务边界在此)。
2. **出网只走 `clients/`**：`api` 调 `vision`/`agent` 必须过 `app/clients/`，统一加超时与降级。
3. **契约唯一**：类型从 `packages/contracts` 生成，禁止在 `schemas/` 手写下放字段。
4. **CV 与推理分离**：`cv/` 产 `.onnx`，`vision/` 只消费；两边依赖互不可见。
5. **gitignore 边界**：`cv/datasets`、`cv/artifacts`、`apps/*/dist`、`*.env` 不入库；权重与数据走对象存储/挂载。

---

## 4. 命名约定

- 服务端口：`api=8080` `vision=8081` `agent=8082`(见各自 `main.py`)。
- 内部路由前缀：`/internal/v1/...`(需 `X-Internal-Token`)；对外 `/v1/...`。
- 表/模型：snake_case 复数表名，ORM 类 PascalCase 单数。
- 知识库文档：`kb-<species>-<topic>.md`，frontmatter 带 `species/category/tags`。

---

## 5. 当前进度对照(速查)

| 目录 | 状态 | 缺什么 |
|---|---|---|
| `apps/mobile` `apps/admin` | ✅ | 接真实后端替换 `mock.js` |
| `services/api` | 🟡 | 52 业务接口、domain/repos、Alembic 迁移 |
| `services/vision` | 🟡 | 真实 `.onnx` 权重 |
| `services/agent`(知识库) | ✅ | 真实 LLM、流式/WS 验证、切分重验 |
| `cv` | ✅ | 真实训练产出权重 |
| `packages/contracts` | ✅ | 接入 codegen 流水线 |
| `infra` | 🟡 | vision/agent 的 Dockerfile |
| `scripts` | ⬜ | 种子/迁移脚本 |

> 下一步优先见 `FEATURE-ROADMAP.md` 的 P0–P5 路线。
