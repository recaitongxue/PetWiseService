# 服务概述

无状态视觉推理服务。输入图片，输出品种与置信度——**它不知道用户、不知道订单**。

与主后端的关键边界：它不在 PostgreSQL 里写任何东西，也不直接调用 LLM。
"看图说话"的文案属于 `services/agent` 的职责。

```
apps/mobile ─▶ services/api ──X-Internal-Token──▶ services/vision ─▶ artifacts/model.onnx
                    │                                   │
                    │                                   └── 由 cv/ 训练并导出
                    └── 超时 3s 即降级，绝不拖垮主链路
```

## 快速开始

```bash
cp .env.example .env
pip install -e .
uvicorn app.main:app --reload --port 8081
```

没有权重时服务仍可启动：`GET /health` 返回 `degraded` 并在 message 里说明原因，
`POST /internal/v1/recognize` 返回 503，由 `services/api` 降级兜底。
这样即使在没装推理依赖的机器上，也能跑通整条链路的冒烟测试。

## 接口

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| GET | `/health` | 无 | 返回加载的模型与 provider（cpu / cuda） |
| POST | `/internal/v1/recognize` | X-Internal-Token | multipart：`image`、`kind`、`topK` |

响应结构与契约 `RecognitionResult` 一致，额外带 `modelVersion` 与 `candidates`（非契约字段）。

## 置信度分级

| 区间 | state | 行为 |
| --- | --- | --- |
| ≥ 0.85 | good | 正常返回 4 项评估指标 |
| 0.45 – 0.85 | watch | 返回指标，标注需关注 |
| < 0.45 | risk | **只返回品种匹配度**，note 明确提示重拍，不虚构评估结果 |

这条规则的意义：与其给出"眼鼻检查正常"这种不负责任的假结论，
不如如实告诉用户没看懂。

## 使用 GPU

```bash
pip install -e ".[gpu]"
export PW_VISION_PROVIDERS=auto   # 检测到 CUDA 会自动优先
```

## 目录说明

```
app/
├── main.py          入口与两个端点
├── config.py        环境变量
├── guard.py         内部 Token 校验
├── registry.py      模型清单解析与按 kind 路由
├── engine.py        会话单例、惰性加载、warmup
├── preprocess.py    EXIF 纠正 + 缩放 + 归一化
├── postprocess.py   softmax / top-k / 置信度分级
└── schemas.py       与契约对齐的结果结构
artifacts/           挂载 cv/artifacts（只读，不入库）
```
