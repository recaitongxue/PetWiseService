# Petwise · 宠物智能服务 APP 平台（前端）

> 本科毕业设计 · 基于**计算机视觉**与**大模型**的宠物智能服务平台
> 技术栈：Vue 3 + Vite + Vue Router（移动优先 / 跨平台）

---

## 一、设计定调（去 AI 味）

| 维度 | 决策 |
|---|---|
| **方向** | 自然有机 + 杂志编辑感：温暖大地色、纸质颗粒、衬线大标题，兼顾"健康可信"与"陪伴温度" |
| **展示字** | Fraunces（带光学尺寸轴的性格衬线）＋ 中文 Noto Serif SC |
| **正文字** | Karla ＋ Noto Sans SC |
| **主色** | 深松绿墨 `#1B2A22` / 暖纸白 `#F2EBDC`（约 60%） |
| **辅助** | 苔绿 `#7E9B78` / 沙色 `#E4D7BE`（约 30%） |
| **强调** | 暖珊瑚 `#E8552B`（约 10%，只给关键动作） |
| **记忆点** | 手绘"爪印圆点眼"品牌标记 ＋ 首屏健康环形 ＋ 取景框有机圆角 |
| **动效** | 编排入场（IntersectionObserver + 错峰）、扫描线、打字气泡，全部支持 `prefers-reduced-motion` 降级 |

---

## 二、功能模块

| 页面 | 路由 | 说明 |
|---|---|---|
| 启动页 | `/` | 品牌 splash，进入首页 |
| 首页 | `/home` | **按时间问候** + **多宠物切换**（联动健康环/趋势/提醒） + 当日疫苗/驱虫提醒 + 周趋势 + 贴士 |
| **拍照识别** | `/recognize` | 取景框 / 拍摄 / **真实相册选图预览** / CV 识别品种·体态·精神（置信度 + 示例库 + **识别记录保存**） |
| **智能问诊** | `/consult` | 大模型兽医对话，**接收拍照识别上下文**、推荐问题、图片问诊、打字动效、**回复后随访建议**、医疗免责声明 |
| **宠物社区** | `/community` | 朋友圈式信息流、**话题筛选**、点赞（修复图标）、**评论底部弹层**、发布（图片画廊） |
| 消息 | `/chat` `/chat/:id` | 会话列表（**未读红点联动**）+ 聊天详情 |
| 我的 | `/profile` | 用户卡 + 我的宠物 + 菜单 |
| 宠物档案 | `/pet/:id` | 健康环 + 数据块 + **体重趋势图** + **免疫/护理日程** + 健康记录时间线 |

> 全局新增轻提示（Toast）系统：发布成功、保存记录、提醒确认等操作均有统一反馈。

---

## 三、本地运行

```bash
cd app
npm install
npm run dev      # 默认 http://localhost:5173
npm run build    # 产物输出到 dist/
```

桌面浏览器打开后会以"手机外壳"居中预览；移动端访问则自动满屏。

---

## 四、跨平台打包（一套代码 → iOS / Android / Web）

当前为 Web（SPA，哈希路由，便于静态托管）。接入原生只需两步：

```bash
npm i -D @capacitor/core @capacitor/cli
npm i @capacitor/ios @capacitor/android
npx cap init petwise com.petwise.app
npm run build
npx cap add ios      # 需要 macOS + Xcode
npx cap add android  # 需要 Android Studio
npx cap sync && npx cap open ios
```

Web 端可直接部署到任意静态托管（含 WorkBuddy 站点发布）。

---

## 五、与后端对接

所有演示数据集中在 `src/data/mock.js`，以 `ref`/函数隔离。接入时：

- **拍照识别**：替换 `Recognize.vue` 中 `capture()` 的模拟延时，改为调用 CV 推理接口（上传图片 → 返回 `{title, sci, confidence, metrics, note}`）。
- **智能问诊**：替换 `Consult.vue` 中 `aiReply()`，改为对大模型接口的流式请求（`fetch` + SSE / WebSocket）。
- **社区 / 消息**：`Community.vue`、`ChatList.vue`、`ChatRoom.vue` 的本地数组改为调用 REST / 实时通信接口。

组件层（图标、卡片、健康环、气泡）与业务解耦，可直接复用。
