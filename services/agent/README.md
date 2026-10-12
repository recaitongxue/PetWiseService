# 服务概述

Petwise 问诊智能体服务。对外不开放，仅接受 `services/api` 的内部调用。

```
用户主诉
  │
  ▼
services/api ──POST /internal/v1/triage──▶ services/agent
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
              规则基线与危险信号      宠物知识库检索（pgvector）   工具：档案/日程/合规
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            ▼
                                    LLM 推理（唯一模型节点）
                                            ▼
                                    合规自检 + 引用来源
                                            ▼
                                    契约结构 TriageResult
```

核心原则：**LLM 只负责理解主诉和组织语言**，
所有确定性信息（年龄、病史、品种易感、是否是急诊）都由规则与知识库决定。

## 快速开始

```bash
cp .env.example .env          # 至少确认 INTERNAL_TOKEN 与 api 服务一致
pip install -e .
uvicorn app.main:app --reload --port 8082
```

未配置 `LLM_API_KEY` 时服务进入 **mock 模式**：链路完整跑通，
结论由 `guardrails` 的规则基线生成——适合答辩演示和前端联调。

## 知识库

```bash
# 1. 起 Postgres（含 pgvector）
docker compose -f ../../infra/compose/compose.dev.yml up -d

# 2. 建表与索引
python -m app.knowledge.cli init-db

# 3. 灌入 services/agent/knowledge_base 下的语料
python -m app.knowledge.cli ingest

# 4. 检索自测
python -m app.knowledge.cli search "猫尿不出来怎么办" --top-k 3
```

语料怎么写：`knowledge_base/README.md`。

### Embedding 三档

| provider | 依赖 | 适用 |
| --- | --- | --- |
| `hash` | 无 | 跑通链路、写测试（**不要用于效果评测**） |
| `local` | `pip install -e ".[embedding]"` | 离线环境、论文实验推荐 |
| `openai` | 无需额外依赖 | 任意 OpenAI 兼容端点 |

改 provider 或模型后必须 `ingest --rebuild`，否则维度不匹配会直接报错。

## 编排引擎

优先使用 LangGraph（`pip install -e ".[graph]"`）；
未安装时自动退化为 `graph/runner.py` 里的顺序执行，**节点与输出完全一致**。
用 `GET /health` 的 `engine` 字段确认当前生效的是哪一种。

## 目录说明

```
app/
├── main.py              服务入口与 SSE 接口
├── config.py            环境变量
├── guard.py             内部 Token 校验
├── guardrails.py        危险信号一票否决 + 处方拦截 + 免责声明
├── schemas.py           与契约对齐的 TriageResult 等
├── graph/
│   ├── state.py         在节点间流动的数据契约
│   ├── nodes.py         六个节点：规则初筛 → 检索 → 工具 → 推理 → 自检 → 组装
│   ├── runner.py        LangGraph / 顺序执行双实现
│   └── report.py        问诊报告生成
├── prompts/v1/*.j2      版本化提示词
├── knowledge/           知识库子系统（模型/切分/向量/检索/灌库/CLI/API）
├── tools/base.py        确定性工具集
├── llm/client.py        LLM 调用与强制 JSON 输出
└── memory.py            会话短期记忆（Redis / 内存）
```
