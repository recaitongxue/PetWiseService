# 契约的代码生成配置

生成器：datamodel-code-generator
依赖已包含在仓库根环境中；在仓库根目录先运行 `uv sync`。

## Python（services/api 的 pydantic schema）

```bash
cd packages/contracts
datamodel-codegen \
  --input openapi.yaml \
  --input-file-type openapi \
  --output ../../services/api/app/schemas/generated.py \
  --target-python-version 3.11 \
  --output-model-type pydantic_v2.BaseModel \
  --use-schema-description \
  --field-constraints \
  --snake-case-field \
  --wrap-string-literal
```

生成的 `generated.py` 不要手改；需要裁剪或重命名请在 `app/schemas/` 里做再导出。

## TypeScript（apps/mobile、apps/admin）

```bash
cd packages/contracts
npx openapi-typescript openapi.yaml \
  -o ../../apps/mobile/src/api/schema.d.ts
cp ../../apps/mobile/src/api/schema.d.ts ../../apps/admin/src/api/schema.d.ts
```

## 约定

1. **接口变更先改 `openapi.yaml`**，再重新生成，最后改代码。
2. 生成物不进 Code Review 的 diff 讨论区，但必须提交，保证 CI 可复现。
3. 手写代码若与契约冲突，以契约为准 —— 不要"顺手"在业务侧加字段。
