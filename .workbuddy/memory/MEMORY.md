# Petwise 项目长期备忘

## 技术栈
- app/：Vue 3 + Vite 5 + Vue Router（哈希路由，移动优先，440px 手机壳居中预览，面向 Capacitor 跨端打包）
- admin/：管理端（公告、反馈与 app 端通过 localStorage 键共享：petwise_announcements / petwise_feedbacks）
- 演示数据集中在 app/src/data/mock.js，用户产生数据与登录态在 data/ops.js（localStorage），接后端时整体替换

## 布局铁律（踩过的坑）
- 外壳 .app-shell 必须用 height（100dvh）锁死而非 min-height；.app-main 必须有 min-height:0 —— 否则 flex 子项被内容撑高、整页滚动、底部 Dock 失效
- 滚动容器是 .app-main 不是 window：切页需手动归零（App.vue 中 watch route.path）；vue-router scrollBehavior 对它无效
- vite.config 不要硬编码 hmr.clientPort（曾导致本地 HMR 完全失效）

## 认证
- 路由 meta.public 放行（splash/login），其余被 beforeEach 拦截到 /login?redirect=
- 登录态 key：petwise_auth；演示登录：任意 1[3-9]xxxxxxxxx 手机号 + 6 位验证码

## 验证方式
- npx vite build 全量编译
- 回归脚本（node 直跑）：.workbuddy/check-nav.cjs、check-auth.cjs（playwright-core + 无头 Chrome）

## 设计体系（2026-10 定稿，源自趋势调研）
- 方向：平静界面 Calm Interface + 低饱和大地色（暖纸白底 + 深松绿墨 + 珊瑚仅作强调）
- 分层靠发丝描边 --hairline（rgba(27,42,34,.07)）而非重阴影；阴影极轻
- 圆角 4 档：10/14/20/28 + pill；不要新增档位
- 渐变只用 3 主（ink/coral/sage）+ 2 低饱和辅色（peach/sand）
- 禁止：纸质噪点纹理、多团渐变光晕、纯黑重阴影、装饰性动效
- 微交互统一：按压 scale(0.978)、150–300ms、--ease-out
- 用户偏好：「高级、干净」= 做减法；新功能先问是否必要，宁可留白

## 参考项目
- E:\PetWise（旧毕设：Flask + Vant 移动端 + Element PC 端）：功能参考源，但 UI 不照搬
- PetWiseService 的 app 已含：识别 / 问诊 / 社区 / 消息 / 档案 / 日程 / 问诊记录 / 收藏
