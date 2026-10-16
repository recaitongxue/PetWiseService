# Petwise 共享基础层（@shared）

移动端与管理端共用的零依赖基础设施。**每个能力只保留这一份实现**，两端通过 Vite alias `@shared` 引用。

## 内容

| 文件 | 说明 |
| --- | --- |
| `src/request.js` | 统一请求层：统一信封 `{code,message,data}`，自动注入 Bearer token，401/20002 静默刷新重试一次，`ApiError` 携带业务 code |
| `src/token.js` | 令牌存储与刷新（localStorage + 单飞刷新） |
| `src/toast.js` | 轻提示全局状态（`showToast`） |
| `src/ToastHost.vue` | 轻提示渲染组件（自包含，不依赖各端图标组件） |

## 约定

- 只放**两端字节级一致**的基础设施；任何一端特有的逻辑放回各端 `src/`
- 修改需同时保证 `apps/mobile` 与 `apps/admin` 构建通过
- 新增导出时同步更新 `src/index.js` 桶文件
