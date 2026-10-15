# PetWiseService

宠物智能服务平台。基于**计算机视觉**（品种识别）与**大语言模型**（问诊智能体），
提供拍照识别、AI 分诊、在线问诊、健康档案与社区等能力。

## 仓库结构

按**部署单元**切分，而非按"前端/后端/算法"角色切分：

```
apps/        可直接运行的产品        mobile（C 端 App）、admin（运营后台）
services/    后端服务，各自独立部署   api（业务网关）、vision（视觉推理）、agent（问诊智能体）
cv/          离线模型研发            训练 · 评测 · 导出 ONNX（产物交付给 vision）
packages/    横切共享               contracts（API 与事件契约）
infra/       部署                   Docker Compose、Nginx
docs/        文档
```

完整说明见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)，接口细节见 [`docs/API.md`](docs/API.md)。

## 请求链路

```
apps/mobile ──▶ nginx ──▶ services/api ──┬──▶ services/vision ──▶ model.onnx
                                         └──▶ services/agent  ──▶ 知识库(pgvector) + LLM
```

`services/api` 是唯一对外网关，其余两个服务不暴露端口，只接受网关的内部调用。

## 快速开始

### 1. 安装 Python 环境

仓库根目录的 `pyproject.toml` 汇总服务、CV 训练和开发依赖，`uv.lock` 固定完整依赖版本。

```bash
uv sync
```

### 2. 起依赖中间件

```bash
docker compose -f infra/compose/compose.dev.yml up -d
```

### 3. 逐个启动服务

```bash
# 业务网关（8080）
uv run --project . --directory services/api uvicorn app.main:app --reload --port 8080

# 视觉推理（8081）
uv run --project . --directory services/vision uvicorn app.main:app --reload --port 8081

# 问诊智能体（8082）
uv run --project . --directory services/agent uvicorn app.main:app --reload --port 8082
```

三个服务都可以**在没有权重、没有数据库、没有 LLM 密钥的情况下启动**，
只是相应地降级。这样本地联调只需要关心自己那一块。

### 4. 前端

```bash
cd apps/mobile && npm install && npm run dev     # http://localhost:5173
cd apps/admin  && npm install && npm run dev     # http://localhost:5174
```

### 5. 知识库（agent 服务）

```bash
uv run --project . --directory services/agent python -m app.knowledge.cli init-db
uv run --project . --directory services/agent python -m app.knowledge.cli ingest
uv run --project . --directory services/agent python -m app.knowledge.cli search "猫尿不出来怎么办"
```

### 6. 全栈部署

```bash
docker compose -f infra/compose/compose.yml up -d
# 有显卡：
docker compose -f infra/compose/compose.yml -f infra/compose/compose.gpu.yml up -d
```

## 技术栈

| 层 | 选型 |
| --- | --- |
| C 端 / 管理端 | Vue 3 + Vite（C 端可 Capacitor 打包） |
| 业务后端 | Python 3.11+ · FastAPI · SQLAlchemy 2 · PostgreSQL · Redis |
| 视觉推理 | ONNX Runtime（不含 torch） |
| 模型训练 | PyTorch + torchvision · 导出 ONNX |
| 问诊智能体 | LangGraph（可选）· pgvector · 可插拔 embedding |
| LLM | 任意 OpenAI 兼容端点，未配置时自动走规则基线 |

## 文档索引

- [`docs/FEATURES.md`](docs/FEATURES.md) **功能文档**：功能清单、交互流程、业务规则、实现状态
- [`docs/DATABASE.md`](docs/DATABASE.md) **数据库设计**：表结构、ER 图、索引、品种识别→建议链路、localStorage 迁移
- [`docs/design/index.html`](docs/design/index.html) **设计文档 · 页面流程图**：29 个页面逐一绘制（入口/流程/分支规则/数据源/出口）+ 全局导航总览；每页带「改进方向」笔记区，可导出 JSON
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) 结构约定、分层纪律、毕业答辩表述
- [`docs/API.md`](docs/API.md) 接口明细（18 组）
- [`packages/contracts/`](packages/contracts) OpenAPI 与事件契约
- [`services/agent/README.md`](services/agent/README.md) 智能体与知识库
- [`services/vision/README.md`](services/vision/README.md) 视觉推理
- [`cv/README.md`](cv/README.md) 模型训练三步走
