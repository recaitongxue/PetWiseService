# PetWiseService 架构与目录规范

> **版本** v1.0 · **最后更新** 2026-10-12 · **状态** 待评审
>
> 本文是仓库唯一的**结构约定**。接口细节一律以 `packages/contracts/openapi.yaml` 为准，
> 本文不重复字段，只定义「代码放哪、谁依赖谁、资源怎么流转」。

---

## 目录

- [1. 结论先行](#1-结论先行)
- [2. 切分原则](#2-切分原则)
- [3. 仓库总览](#3-仓库总览)
- [4. 在线层](#4-在线层)
  - [4.1 apps/mobile 与 apps/admin](#41-appsmobile-与-appsadmin)
  - [4.2 services/api 业务后端](#42-servicesapi-业务后端)
  - [4.3 services/vision 视觉推理](#43-servicesvision-视觉推理)
  - [4.4 services/agent 问诊智能体](#44-servicesagent-问诊智能体)
- [5. 离线层 cv/ 模型研发](#5-离线层-cv-模型研发)
- [6. 横切层](#6-横切层)
- [7. 关键调用链路](#7-关键调用链路)
- [8. 技术选型与环境](#8-技术选型与环境)
- [9. 本地开发与部署](#9-本地开发与部署)
- [10. 降级方案：当你不需要三个进程](#10-降级方案当你不需要三个进程)
- [11. 落地路线](#11-落地路线)
- [12. 答辩表述参考](#12-答辩表述参考)
- [附录 A：现有目录迁移命令](#附录-a现有目录迁移命令)

---

## 1. 结论先行

四个顶层概念（前端 / 后端 / CV / 智能体）**方向正确**，但直接平铺成四个目录会有三个问题：

| 直觉 | 问题 | 修正 |
| --- | --- | --- |
| "前端一个目录" | C 端 App 与运营后台是两套独立产物，域名、打包、权限模型都不同 | 都放进 `apps/`，平级命名 |
| "CV 模型一个目录" | 训练（离线、跑几小时、torch）与推理（在线、毫秒响应、onnxruntime）生命周期冲突，混合会导致生产镜像含 14 万张数据集和数 GB 的 CUDA 依赖 | 拆成 `cv/`（离线研发）与 `services/vision`（在线服务），二者是**生产—消费**关系 |
| "智能体一个顶层目录" | 它是有状态、长连接、需独立扩容的在线进程，放顶层会绕过鉴权与网关直接对外 | 收进 `services/agent` |

**一句话原则**：第一刀按**部署单元**切（运行时边界），第二刀按**职责**切（层内分层）。

---

## 2. 切分原则

### 2.1 一个模块要不要独立成服务

同时用这三条判断，命中两条以上就拆：

| 判据 | services/vision | services/agent | 业务 CRUD |
| --- | :---: | :---: | :---: |
| 技术栈异构（与宿主不同 runtime / 需 GPU） | ✅ | ⚠️ | ❌ |
| 故障会拖垮主链路（长耗时 / 长连接 / 显存占用） | ✅ | ✅ | ❌ |
| 伸缩粒度不同（按 QPS 单独扩容、按显存单独调度） | ✅ | ✅ | ❌ |
| **结论** | **必须独立** | **建议独立** | **留在主后端** |

> 注：`services/vision` 与 `services/agent` 虽然同为 Python，但与主后端的**依赖体积、资源画像、失败模式**完全不同。
> 强行合并会让主后端镜像被 torch/CUDA 撑到数 GB，且一次显存 OOM 会带走全部业务接口。

### 2.2 依赖方向必须单向

```
apps/*  →  services/api  →  services/{vision,agent}
                         ↘  cv/           （离线，不在线依赖）

apps/*  →  packages/contracts        （只读契约）
services/*  →  packages/contracts    （生成类型 / schema）
```

硬性禁止：

- `services/vision`、`services/agent` **不得**反向 import `services/api` 的任何模块——需要业务数据时由 `services/api` 通过**工具接口**喂给它（见 4.4 的工具设计）。
- 前端、后端都不得直接读 `cv/artifacts`。权重只经由 `services/vision` 提供。
- `cv/` 不 import 任何 `services/*`，它是纯粹的离线工程。

---

## 3. 仓库总览

```
PetWiseService/
├── apps/                        # 可直接运行 / 打包的客户端
│   ├── mobile/                  # C 端 App（Vue3 + Vite + Capacitor）
│   └── admin/                   # 运营后台（Vue3 + Vite）
│
├── services/                    # 后端服务，每个子目录一个部署单元
│   ├── api/                     # 业务后端（FastAPI）· 唯一对外网关
│   ├── vision/                  # 视觉推理服务（FastAPI + ONNX Runtime）
│   └── agent/                   # 问诊智能体服务（FastAPI + LangGraph + 知识库）
│
├── cv/                          # 离线层：模型训练和导出，不对外提供端口
│   ├── configs/                 # 训练超参、数据增强、导出配置
│   ├── src/{data,models,train,eval,export}/
│   ├── notebooks/               # 仅探索性实验，禁止进流水线
│   ├── scripts/                 # split.sh / train.sh / export.sh
│   ├── datasets/                # （gitignore）原始数据与处理后数据
│   ├── artifacts/               # （gitignore）best.pt / model.onnx / labels.json
│   └── README.md                # 如何复现训练结果
│
├── packages/                    # 横切共享包
│   └── contracts/               # API 与事件的单一事实源
│       ├── openapi.yaml         # 11 tag / 52 接口 / 30 schema
│       ├── events/frames.yaml   # WebSocket 推送帧 schema（API.md 第 5 章）
│       └── codegen/             # 类型 / DTO 生成配置
│
├── infra/                       # 基础设施
│   ├── compose/                 # compose.dev.yml / compose.yml / compose.gpu.yml
│   ├── docker/                  # Dockerfile.api / Dockerfile.vision / Dockerfile.agent
│   └── nginx/                   # 反向代理与静态资源
│
├── scripts/                     # 仓库级脚本（初始化、备份、批量评测）
├── docs/                        # 文档
│   ├── ARCHITECTURE.md          # 本文
│   └── API.md                   # 接口说明（面向阅读，非契约）
└── README.md
```

---

## 4. 在线层

### 4.1 apps/mobile 与 apps/admin

两者是**同仓库、同技术栈、不同产物**的关系，互不 import，共享的只有设计 token 与图标资源。

| | apps/mobile | apps/admin |
| --- | --- | --- |
| 路由 | 哈希路由（Capacitor 静态托管） | History 路由 |
| 视口 | 移动优先，440px 手机壳预览 | 桌面自适应 |
| 鉴权 | 用户 Token | 管理员 Token |
| 数据来源 | `/api/v1/*` | `/api/v1/admin/*` |

现状已满足，迁移时只需改路径（保持 `src/` 内部结构不变），注意同步修改 `package.json` 的 `name` 与 `vite.config.js` 的输出目录。

> 后续若要加小程序（如 `apps/miniprogram`），直接在 `apps/` 下新增即可，不会打乱现有结构——这是当初把 `app/` 改名的重要原因。

### 4.2 services/api 业务后端

角色的准确定位：**它是对外的唯一网关 + 全部业务数据的持有者**。`vision` 和 `agent` 都不直接面对客户端。

```
services/api/
├── app/
│   ├── main.py                  # FastAPI 入口、lifespan、全局异常处理器
│   ├── core/
│   │   ├── config.py            # pydantic-settings，读环境变量
│   │   ├── logging.py           # 结构化日志，透传 traceId
│   │   ├── errors.py            # AppError 与业务错误码（对齐 contracts 1.4）
│   │   ├── security.py          # JWT 签发校验、权限依赖
│   │   ├── deps.py              # 依赖注入：DB session、当前用户
│   │   └── envelope.py          # 统一响应包 {code,message,data,timestamp,traceId}
│   ├── api/
│   │   ├── middleware/          # traceId 注入、请求耗时、CORS、限流
│   │   └── routers/             # 按 contracts 的 tag 一对一拆分（见下表）
│   ├── domain/                  # 实体、值对象、纯领域规则（不依赖框架）
│   ├── services/                # 用例编排：事务边界在这一层
│   ├── repos/                   # 数据访问，屏蔽 ORM 细节
│   ├── models/                  # SQLAlchemy ORM 模型
│   ├── schemas/                 # pydantic DTO（字段口径以 contracts 为准）
│   ├── clients/                 # 调用内部服务的客户端（唯一的出网口）
│   │   ├── vision.py            # VisionClient：识别 + 超时降级
│   │   ├── agent.py             # AgentClient：分诊流式的转发
│   │   └── storage.py           # 对象存储（MinIO / COS）
│   ├── ws/                      # WebSocket 网关（问诊室、IM）
│   └── tasks/                   # 异步任务：提醒推送、报告生成
├── migrations/                  # alembic
├── tests/
├── pyproject.toml
└── Dockerfile
```

**路由与 contracts tag 的映射**（契约 11 个 tag、52 个接口）：

| router | tag | 主要路径 |
| --- | --- | --- |
| `auth.py` | auth | `/auth/*`、`/users/me` |
| `pets.py` | pets | `/pets`、`/pets/{id}`、`/pets/{id}/health-trend`、`/weights` |
| `records.py` | pets | `/pets/{id}/records`、`/records/{id}` |
| `schedule.py` | schedule | `/schedule*`、`/pets/{id}/reminders` |
| `home.py` | home | `/home` |
| `content.py` | content | `/announcements`、`/feedbacks`、`/breeds`、`/favorites` |
| `recognition.py` | recognition | `/recognitions` |
| `consult.py` | consult | `/consult/*` |
| `doctors.py` | consult | `/doctors*`、`/doctors/{id}` |
| `community.py` | community | `/posts*` |
| `im.py` | im | `/conversations*` |
| `files.py` | files | `/files` |
| `admin.py` | admin | `/admin/*` |

**三条必须守住的分层纪律**：

1. **routers 不得直接 import repos**。路由只做参数校验与调用转发，业务逻辑一律经 `services/`。
2. **IO 出网只能走 `clients/`**。禁止在 service 里裸写 `httpx.post`，否则超时、重试、降级、埋点会散落各处。
3. **事务边界在 services 层**，repos 不开启事务。

**统一响应与错误**：契约定义了 `{code, message, data, timestamp, traceId}` 信封，实现上收敛到两个出口：

```python
# 成功：所有 router 直接 return 业务数据，由路由装饰器统一包装
@router.post("/recognitions", response_model=Envelope[RecognitionResult])
async def recognize(file: UploadFile, svc: RecognitionService = Depends()):
    return await svc.recognize(file)          # envelope.py 负责包装

# 失败：抛 AppError，全局异常处理器统一转信封
raise AppError(code=40201, message="今日识别额度已用完", status=429)
```

好处是前端 `api/request.js` 只需认一套结构，`message` 可直接上 toast。

### 4.3 services/vision 视觉推理

定位：**无状态的计算服务**。它不知道用户、不知道订单，输入图片，输出品种与置信度。

```
services/vision/
├── app/
│   ├── main.py                  # FastAPI，仅暴露 /internal/v1/recognize 与 /health
│   ├── engine.py                # 推理会话单例，lifespan 阶段预热模型
│   ├── preprocess.py            # EXIF 方向纠正、resize、归一化
│   ├── postprocess.py           # top-k → 品种 id → 置信度分级（高/中/低）
│   ├── registry.py              # 模型版本、labels.json 与品种词典的映射
│   ├── schemas.py               # RecognitionResult（对齐 contracts 同名 schema）
│   ├── guard.py                 # 内部 Token 校验，禁止外网直连
│   └── telemetry.py             # 推理耗时、显存占用、失败原因计数
├── artifacts/                   # 启动时挂载 cv/artifacts（只读）
├── pyproject.toml               # 只依赖 onnxruntime + numpy + pillow，不含 torch
└── Dockerfile
```

关键设计：

- **不装 torch**。训练产物统一导出为 ONNX / TorchScript，推理镜像只有 ONNX Runtime，体积可从数 GB 降到数百 MB。
- **kind → 模型路由**。契约里识别涉及犬种/猫种等多类目，用 `registry.py` 按 `kind` 选择对应 session，避免一次加载全部模型。
- **超时降级**。业务侧给 3s 预算，超时即返回低置信度结果并由 `services/api` 兜底文案，绝不阻塞主链路。
- **绝不直连 LLM**。识别结果就是结构化分类 + 置信度，"看图说话"的文案生成属于 `services/agent` 的职责。

### 4.4 services/agent 问诊智能体

定位：**有状态的编排服务**。这是全文唯一的 LLM 所在层（除对用户侧的文案润色）。

```
services/agent/
├── app/
│   ├── main.py                  # SSE 流式接口 + 健康检查
│   ├── graph.py                 # LangGraph 状态机定义
│   ├── nodes/
│   │   ├── triage.py            # 意图识别与科室路由
│   │   ├── gather.py            # 并行拉取宠物档案、病历、品种知识
│   │   ├── reason.py            # 生成结构化建议（强制 JSON schema 输出）
│   │   ├── critique.py          # 自检：是否越界、是否需要转人工
│   │   └── format.py            # 组装前端卡片所需的字段
│   ├── tools/                   # 供 LLM 调用的确定性接口
│   │   ├── pet_profile.py       # 查宠物档案
│   │   ├── medical_records.py   # 查历史病历与体重趋势
│   │   ├── breed_kb.py          # 品种易感疾病知识库（RAG）
│   │   └── schedule.py          # 建议生成提醒日程
│   ├── prompts/
│   │   └── v1/                  # 版本化提示词模板（Jinja），含版本号
│   ├── rag/
│   │   ├── embeddings.py        # bge-small-zh 等中文向量模型
│   │   ├── indexer.py           # 离线灌库脚本
│   │   └── retriever.py         # 混合检索 + rerank
│   ├── guardrails.py            # 医疗免责、越界拒答、来源引用强制
│   ├── memory.py                # 会话短期记忆（Redis）
│   └── tracing.py               # LangSmith / OTel 链路
├── pyproject.toml
└── Dockerfile
```

**最重要的架构决策：LLM 不是主力，工具才是。**

```
                    ┌──────────────────────────────┐
   用户主诉  ──▶    │ triage → gather → reason → format │  ──▶  结构化问诊建议
                    └──────┬──────────┬────────────┘
                           │          │
                    LangGraph 编排   LLM 节点（仅 2 个）
                           │
              tools/ ── 确定性数据：档案 / 病历 / 品种库
```

- **确定性信息（年龄、体重、疫苗史、品种易感病）必须来自工具查询**，不允许 LLM 凭记忆生成。这是毕设里最能体现工程性的地方，也是防幻觉的根本手段。
- **只有"意图理解"和"语言组织"交给 LLM**，其余全部是传统代码。
- 输出走**强制 JSON Schema**（而非自由文本），前端才能渲染 `TriageCard` 那样的结构化卡片。
- `guardrails.py` 是答辩必须讲的一环：医疗免责声明、越界（如要求开处方药）拒答、每条结论附数据来源。

**为什么不放在 `services/api` 里**：它有独立的失败模式（LLM 超时、限流、Token 成本）和独立的伸缩需求（按并发会话数扩容），且需要独立的重试/降级策略。

### 4.5 知识库子系统

这是问诊质量的**根本保障**，也是本仓库唯一自己维护的数据资产。

#### 为什么必须有它

通用大模型对"某个犬种的易感肾病""猫尿闭的黄金处置时间"这类细节并不可靠，
且大量宠物医疗知识属于垂直领域。没有知识库时，模型只能靠参数记忆作答——
这正是幻觉的来源。

知识库的作用不是"让回答更好听"，而是**让每条结论可核验**：回答里每个引用都指向
`kb_chunk` 表里的一行，能被打开、能被质疑、能被更新。

#### 数据流

```
knowledge_base/*.md ──loaders──▶ 结构化语料
        │
        ├──chunkers（标题优先 + 滑窗兜底）──▶ 若干 Chunk
        │
        ├──embeddings（hash / local / openai）──▶ 向量
        │
        └──▶ kb_document + kb_chunk（pgvector，HNSW 索引）

查询侧：
    用户主诉 ──embed──▶ 向量粗召回(≤30) ──关键词补充──▶ 混合打分
        │
        └──rerank（启发式 / cross-encoder）──▶ 阈值过滤 ──▶ 同文档去重 ──▶ top-k
                                                              │
                                                              ▼
                                              带来源标注的上下文 → 提示词
```

#### 表结构

| 表 | 作用 | 关键字段 |
| --- | --- | --- |
| `kb_document` | 文档元数据 | `source_type`、`species`、`tags`、`version` |
| `kb_chunk` | 最小检索单元 | `embedding vector(dim)`、`heading`、`content`、`meta` |

为什么分块表独立：检索的最小粒度是语义完整的段落而非整篇文档；回答需要引用到具体段落；
文档更新时按 `document_id` 整体替换即可。

#### 切分策略

标题优先（`## xxx` 切开）→ 段落合并到接近 380 字 → 超长才二次滑窗（overlap 60）。

直接按固定长度切会让一个"必须就医"的段落被拦腰截断，
检索到的是半句话——这是很多 RAG 系统召回差的真实原因。

#### Embedding 三档

| provider | 依赖 | 什么时候用 |
| --- | --- | --- |
| `hash` | 无 | 跑通链路、写单测。**不要用于效果评测** |
| `local` | sentence-transformers | 离线环境、论文实验（推荐 `bge-small-zh-v1.5`） |
| `openai` | 无需额外依赖 | 任意 OpenAI 兼容端点 |

换 provider 或模型 **必须 `ingest --rebuild`**：向量维度不一致会直接写库失败，
这是刻意设计的强约束——避免"新模型的查询去搜旧模型的向量"这种静默错误。

#### 混合检索与重排

粗召回 = 向量相似度；Python 侧再叠加关键词覆盖率（针对中文分词的现实妥协，
Postgres 的 `to_tsvector` 对中文几乎无效）。混合权重在 `.env` 可调。

重排默认用零依赖的启发式（标题命中 +0.15、短语命中 +0.10、覆盖度加权、
按 source_type 给 first_aid/disease 更高先验），有 GPU 时可切 `cross-encoder`。

#### 日常操作

```bash
python -m app.knowledge.cli init-db                  # 建表 + HNSW 索引
python -m app.knowledge.cli ingest --rebuild         # 灌库（幂等，同 id 整篇替换）
python -m app.knowledge.cli search "猫尿不出来"       # 召回自测
python -m app.knowledge.cli stats                    # 健康度
```

语料怎么加：`services/agent/knowledge_base/README.md`。一句话概括——
**往 `knowledge_base/<分类目录>/` 里丢一个带 front matter 的 Markdown 就行，目录名即分类。**

---

## 5. 离线层 cv/ 模型研发

`cv/` 存在的唯一目的：**产出一个 `model.onnx` 和一份 `labels.json`**，然后交付给 `services/vision`。它永远不对外提供端口。

```
cv/
├── configs/
│   ├── dataset.yaml             # 数据路径、类别清单、划分比例
│   ├── train.yaml               # backbon、epochs、lr、batch size
│   ├── augment.yaml             # 增强策略
│   └── export.yaml              # 导出精度、动态轴、opset 版本
├── src/
│   ├── data/
│   │   ├── dataset.py           # Dataset / DataLoader
│   │   ├── transforms.py        # 训练与验证的变换
│   │   └── split.py             # 数据集划分
│   ├── models/
│   │   ├── backbones.py         # ResNet / EfficientNet / ConvNeXt
│   │   ├── heads.py             # 分类头
│   │   └── factory.py           # 按配置组装
│   ├── train/
│   │   ├── trainer.py           # 训练循环、AMP、checkpoint
│   │   └── loops.py             # 单 epoch 的训练与验证
│   ├── eval/
│   │   ├── evaluate.py          # top-1 / top-5 / 混淆矩阵
│   │   └── report.py            # 生成 Markdown 评测报告（直接用于论文）
│   └── export/
│       ├── to_onnx.py           # torch → onnx
│       └── quantize.py          # 动态量化
├── notebooks/                   # EDA 与可视化，明确不进 CI
├── scripts/{train.sh,eval.sh,export.sh}
├── datasets/                    # （gitignore）
├── artifacts/                   # （gitignore）best.pt / model.onnx / labels.json
├── tests/
├── pyproject.toml
└── README.md                    # 数据准备 → 训练 → 导出，一步不漏
```

三条纪律：

1. **notebooks 永远是探索区**。任何被确认有效的逻辑，必须重写进 `src/`，`src/` 是唯一可复现的路径。
2. **配置与代码分离**。改超参只改 `configs/*.yaml`，不碰 Python 文件——这样实验记录是可追溯的，论文里也好列表。
3. **每次导出都带版本号**。文件名形如 `model-v3.onnx`，并与 `registry.py` 和契约里的 `modelVersion` 字段三方对齐，便于线上回滚。

---

## 6. 横切层

### 6.1 packages/contracts —— 单一事实源

`docs/openapi.yaml`（11 tag / 52 接口 / 30 schema）已迁入此处。它就是契约本身，
前端 TS 类型与后端 pydantic 模型都从它生成。

```
packages/contracts/
├── openapi.yaml                 # 前后端的唯一事实依据
├── events/frames.yaml           # WebSocket 推送帧定义（API.md 第 5 章）
├── codegen/README.md            # datamodel-codegen / openapi-typescript 命令
└── README.md                    # 改契约的完整流程
```

约定：**接口变更先改这里，再改代码**。前端 TS 类型与后端 pydantic 模型都由它生成，避免双份定义漂移。手写代码若与契约冲突，以契约为准并重新生成。

### 6.2 infra

```
infra/
├── compose/
│   ├── compose.dev.yml          # postgres + redis + minio + qdrant（本地开发依赖）
│   ├── compose.yml              # CPU 版全栈（毕设演示够用）
│   └── compose.gpu.yml          # 有显卡时叠加 nvidia runtime
├── docker/
│   ├── Dockerfile.api / .vision / .agent
│   └── nginx/                   # 反向代理、静态托管、WebSocket 升级
└── README.md
```

拆分 compose 文件的理由：`compose.yml` 让没有 GPU 的机器也能一键起全栈（ONNX Runtime 支持 CPU 推理，只是慢），答辩演示不依赖实验室显卡。

---

## 7. 关键调用链路

### 7.1 拍照识别

```
apps/mobile
  │ POST /api/v1/files            先传图拿到 fileKey
  │ POST /api/v1/recognitions     { fileKey, kind }
  ▼
services/api · routers/recognition.py
  │ 校验额度 → VisionClient.recognize()  [3s 超时 + 重试 1 次]
  ▼
services/vision · /internal/v1/recognize
  │ preprocess → ONNX session → postprocess
  │ 返回 { breedId, confidence, candidates[], modelVersion }
  ▼
services/api
  │ 落库 recognition 记录 → 关联宠物 → 返回 RecognitionResult
```

降级路径：vision 超时或不可用时，`services/api` 返回低置信度兜底结果并在 `message` 里提示，绝不返回 500。

### 7.2 AI 问诊

```
apps/mobile
  │ POST /api/v1/consult/triage   SSE 流式接收
  ▼
services/api · routers/consult.py
  │ 鉴权 + 扣额度 + 组装上下文（userId, petId）
  │ AgentClient.stream()          [带 traceId]
  ▼
services/agent · graph
  │ triage → gather(tools 并行查) → reason(LLM) → critique → format
  │ 每产出一段就 yield 一个 SSE 帧
  ▼
services/api
  │ 逐帧转发给客户端（不改内容）
  │ 流结束后：落库 triage 结果、可选生成 diseaseReminder 日程
```

`services/agent` 拿不到用户 Token，拿不到数据库连接——它只拿到 `services/api` 显式传来的上下文。这条边界保证了权限不会在 AI 层被绕过。

---

## 8. 技术选型与环境

| 层 | 选型 | 理由 |
| --- | --- | --- |
| C 端 | Vue 3 + Vite + Capacitor | 现状，可直接打包 iOS / Android / Web |
| 管理端 | Vue 3 + Vite | 与 C 端共享设计体系 |
| 业务后端 | Python 3.11 + FastAPI | 与 AI 侧同栈，依赖复用；异步支持 WebSocket 与 SSE |
| ORM / 迁移 | SQLAlchemy 2 + Alembic | |
| 关系库 | PostgreSQL 15 | pgvector 可直接承载 RAG 向量，省一个组件 |
| 缓存 / 队列 | Redis | 会话记忆、额度计数、Celery broker |
| 对象存储 | MinIO（本地）/ COS（生产） | 接口一致，切换只改环境变量 |
| 向量检索 | pgvector 起步，规模上再换 Qdrant | 毕设规模不必引入额外服务 |
| CV 推理 | ONNX Runtime | 推理镜像不含 torch，CPU/GPU 同代码 |
| CV 训练 | PyTorch + timm | |
| 智能体编排 | LangGraph | 状态机比裸 Chain 可控，节点可单测 |
| 复杂度 | Python 3.13 起 LiteLLM 统一多厂商 | 便于后期换模型或做降级兜底 |

> Python 版本建议统一 3.11 或 3.12（`cv/` 依赖的 torch 对新版本兼容滞后），三个 Python 服务共用一套 `pyproject.toml` 规范。

---

## 9. 本地开发与部署

### 9.1 目录职责对应的启动方式

```bash
# 1. 起依赖
docker compose -f infra/compose/compose.dev.yml up -d

# 2. 三个后端服务各自独立启动，互不干扰
cd services/api    && uvicorn app.main:app --reload --port 8080
cd services/vision && uvicorn app.main:app --port 8081
cd services/agent  && uvicorn app.main:app --port 8082

# 3. 前端
cd apps/mobile && npm run dev      # vite 已配 /api 代理到 8080
cd apps/admin  && npm run dev
```

### 9.2 生产部署

```bash
docker compose -f infra/compose/compose.yml up -d            # CPU 版
docker compose -f infra/compose/compose.yml \
               -f infra/compose/compose.gpu.yml up -d        # 有显卡时
```

对外只暴露 nginx 的 80/443。`services/vision` 与 `services/agent` 的端口**不映射到宿主机**，只在 compose 内部网络中可被 `services/api` 访问，另加一层内部 Token 校验。

这套布局带来的直接收益：**改模型不用重新构建整站**，只需替换 `cv/artifacts` 中的 onnx 并重启 vision；同理，改提示词只重启 agent。

---

## 10. 降级方案：当你不需要三个进程

架构是分层的，但部署粒度可以按进度收放。如果时间紧张，推荐这个形态：

```
services/api/
└── app/
    ├── modules/vision/          # 直接 import src/ 的推理代码
    ├── modules/agent/           # LangGraph 编排
    └── ...
```

即：**目录和依赖方向照本文保持，只是用一个进程加载三个模块**。

- 前提：接受推理用 CPU 或轻量 GPU、不做独立扩容、主进程因显存 OOM 会影响全部接口。
- 代价：镜像含 torch（较大），且模型重载需要重启整个服务。
- 迁移成本：因为依赖方向已经是单向的，未来拆开只需把 `modules/*` 换成 `clients/*` 的 HTTP 调用，**业务 services 层几乎不用改**。

判断标准很简单：**答辩演示是单机还是有服务器**。单机演示完全可以三合一；只要有独立部署，建议一开始就拆开。

---

## 11. 落地路线

| 阶段 | 内容 | 状态 |
| --- | --- | :---: |
| P0 结构 | 目录迁移、删 `fronted/`、修正配置、更新 `.gitignore` | ✅ |
| P1 契约 | `docs/openapi.yaml` → `packages/contracts/`，补 events + codegen 说明 | ✅ |
| P2 骨架 | `services/api` 落地 core（配置、日志、信封、错误码、中间件）+ 健康检查 + clients 层 | ✅ |
| P3 CV | `cv/` 目录成型：切分 / 训练 / 评测 / 导出三步走 | 骨架就绪 |
| P4 vision | `services/vision` 完整骨架（registry / engine / 预处理 / 分级），**等权重** | 骨架就绪 |
| P5 agent | LangGraph 编排 + 知识库 + 工具 + guardrails | ✅ |
| P6 业务 | 按 tag 逐个补齐 `services/api` 的 13 个 router | 待补 |
| P7 编排 | compose 三套 + nginx + 三份 Dockerfile | ✅ |

下一步建议从 **P6** 开始：按 openapi tag 逐个补 router，每个 router 照
`app/api/routers/demo.py` 的写法（成功 `ok()`、失败 `AppError`、AI 调用走 clients）。

---

## 12. 答辩表述参考

**问：为什么不用单体？**
> 因为三个部分的资源画像和失败模式不同。视觉推理需要 GPU 且单次耗时在数百毫秒量级，可能 OOM；问诊是长连接流式输出，受上游 LLM 限流影响；业务 CRUD 是毫秒级的短请求。三者共进程会导致一次显存溢出让整个 App 不可用。拆分后可以对推理服务单独做超时降级——识别失败时用户可以继续用问诊和社区。

**问：AI 到底在系统的哪里？**
> 两处，且性质不同。一是视觉侧的深度学习分类模型，训练在离线目录 `cv/`，导出 ONNX 后由 `services/vision` 加载提供推理；二是问诊侧的大模型编排，在 `services/agent`，用 LangGraph 定义状态机。两者都不直接面向客户端，统一由 `services/api` 作为网关调度。

**问：怎么防止大模型胡说？**
> 三层约束。第一，确定性信息（宠物年龄、体重趋势、既往病历、品种易感病）全部通过工具查询真实数据，不交给模型生成记忆；第二，输出强制 JSON Schema，不符合结构的回答会被拒绝重试；第三，guardrails 做医疗免责、越界拒答，每条结论附数据来源。模型只负责两件事：理解用户主诉的意图，和把结构化结果组织成用户能读的语言。

**问：训练和上线是怎么衔接的？**
> 训练是一次性离线过程，唯一产物是分量化的 ONNX 权重和标签文件，带版本号。上线时把它挂载到推理服务的只读目录，推理服务从 registry 里按版本号加载。所以替换模型不需要重新构建整个系统，也不需要重启业务服务。

---

## 附录 A：目录迁移记录（已完成）

以下操作已在 `dev` 分支执行完毕，记录在此便于复现与回溯：

```bash
mkdir -p apps services scripts packages/contracts infra/compose infra/docker infra/nginx
git mv app        apps/mobile
git mv admin      apps/admin
git mv model      cv                  # 14 万张数据集随之移动（已在 gitignore 中）
git mv model/data … -> cv/datasets    # 直接 mv，未被 Git 跟踪不会产生 rename 记录
git mv docs/openapi.yaml packages/contracts/openapi.yaml
rmdir fronted backend                 # 拼写错误的空目录 / 已被 services/api 取代
```

Windows 上 `git mv model cv` 可能因句柄占用失败，先 `mv model/data cv/datasets`
把数据搬走即可，`git mv` 只负责被跟踪的 `.gitkeep`。

随后同步修改的内容：

| 文件 | 改动 |
| --- | --- |
| `.gitignore` | `model/data/` → `cv/datasets/` + `cv/artifacts/` + `cv/runs/`，并补齐 Python 生态忽略项 |
| `apps/mobile/package.json` | `name` 改为 `petwise-mobile` |
| `docs/API.md` | 前端路径引用 `app/src/` → `apps/mobile/src/` |
| 各 `README.md` | 与实际路径对齐 |

> 两个前端各自拥有 `dist/`，互不冲突，因此**不需要**改 `outDir`。

迁移后 `apps/mobile` 与 `apps/admin` 的 `npm run build` 均已验证通过。
