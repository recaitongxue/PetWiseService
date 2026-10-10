# Petwise Admin · 管理端 Web 控制台

毕业设计「基于计算机视觉与大模型的宠物智能服务 APP 平台」的**运营管理端**。
与用户端 App（`../app`）同一品牌设计语言（暖纸白 + 深松绿 + 暖珊瑚，Fraunces 编辑感），
采用桌面后台的「工业实用」方向：深色侧边栏 + 发丝线表格 + 等宽数字。

## 运行

```bash
cd admin
npm install --ignore-scripts
npm run dev      # http://localhost:5174（用户端 App 在 5173）
npm run build
```

**演示账号：`admin / petwise`**（localStorage 模拟登录守卫，接入后端后替换为 token 校验）

## 功能模块（纯管理视角，不含任何 C 端用户功能）

| 模块 | 路由 | 说明 |
|---|---|---|
| 登录 | `/login` | 演示鉴权 + 路由守卫 |
| 数据看板 | `/dashboard` | 核心指标卡（用户/宠物/今日识别/今日问诊）、近 7 日 CV+LLM 调用量 SVG 折线图、品种识别分布、运营速览入口 |
| 用户管理 | `/users` | 账号治理：搜索/筛选、冻结恢复、详情抽屉（含名下宠物档案、重置密码、数据导出） |
| 识别记录 | `/records` | CV 调用日志、置信度条（低于阈值自动标记人工复核） |
| 内容审核 | `/moderation` | 社区帖子人工审核（通过/驳回）、敏感词初筛提示 |
| 问诊记录 | `/consults` | 大模型会话日志、轮次/模型/转人工状态 |
| 公告管理 | `/announce` | 发布/编辑/上下线平台公告，App 首页公告条实时同步 |
| 用户反馈 | `/feedback` | 处理 App 端「意见反馈」（问题/建议分类、待处理徽标、标记完成） |
| 系统设置 | `/settings` | 模型与服务配置（CV 阈值/LLM 选择/免责声明/注册开关）、敏感词库 CRUD、管理员角色权限 |

> 设计原则：宠物档案隶属于用户，作为用户详情抽屉的子视图呈现，不设独立 CRUD 页；
> 管理端只做"治理与监控"（看板、审核、AI 服务质量复核、系统配置、权限），不做发帖/问诊等用户功能。

## 架构

- Vue 3 + Vite + Vue Router（哈希路由），零 UI 库依赖，全部手写组件与 SVG 图表。
- 全局 Toast（`composables/toast.js`）、`v-reveal` 入场动效（`prefers-reduced-motion` 降级）。
- 演示数据集中在 `src/data/admin.js`，公告与反馈使用 `src/data/ops.js`（localStorage 持久化，与 App 端共用 `petwise_announcements` / `petwise_feedbacks` 键，双端演示闭环）。

## 参考项目「取长补短」说明

参考了 `D:\recaitx\PetWise`（Element Plus 桌面端单后台）：

- **吸收**：品种百科知识库驱动（App 端 `/breed/:id` 百科页 + 识别结果一键跳转）、公告运营与用户反馈双闭环（本端公告管理 + 反馈处理两页）。
- **规避**：emoji 当作 imagery、Element 桌面式堆表单、仅 Web 单端、无社区/聊天能力。
- **不做**：批量识别（App 单拍场景弱）、Prompt/限流等管理页（与「系统设置」职责重复）。
