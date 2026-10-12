# packages/contracts

**前后端共用的唯一契约来源。** 所有类型、DTO、事件定义都从这里出发。

## 为什么单独拎出来

前后端各写一份类型定义，短期很快，长期必然漂移：后端改了字段名，
前端要等到运行时报错才发现。把契约变成单一事实源 + 代码生成，
这种问题在**编译期**就会暴露。

## 内容

| 文件 | 作用 |
| --- | --- |
| `openapi.yaml` | HTTP 接口契约：11 个 tag、52 个接口、30 个 schema |
| `events/frames.yaml` | WebSocket 推送帧契约（对应 `docs/API.md` 第 5 章） |
| `codegen/README.md` | 生成 TS 类型与 Python 模型的命令 |

## 工作流

```
需求变更
  │
  ▼ 先改这里
openapi.yaml
  │
  ├──────────── datamodel-codegen ────────▶ services/api/app/schemas/generated.py
  │
  └──────────── openapi-typescript ───────▶ apps/*/src/api/schema.d.ts
```

## 什么时候改流水线 vs 改文档

- 字段、路径、枚举、错误码变了 → **必须**改 `openapi.yaml`
- 只是补充说明或示例 → 改 `docs/API.md` 即可

## 校验

```bash
npx @redocly/cli lint openapi.yaml
```
