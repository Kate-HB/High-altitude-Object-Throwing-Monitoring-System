# 刘康 - 前端开发

## 基本信息
- 角色：前端负责人
- 分支：`feature/liukang`
- 工作目录：`frontend/`
- 框架：Vue 3 + Element Plus + Axios + ECharts

## 已完成

### 6月24日
- 页面路由设计（8个页面）
- 页面结构草图

### 6月25日
- Vue Router配置（8条路由 + auth守卫）
- 登录页 `LoginView.vue`
- 系统首页 `HomeView.vue`（状态卡片+健康检查）
- MainLayout（侧边栏+顶栏）
- Axios封装：请求拦截器（token注入）+ 响应拦截器（统一解包 `{code, data, message}`）
- 全局样式（深色科技风）

### 6月26日
- `api/videos.js` — 视频上传/分析/查询API
- `VideoAnalysisView.vue` — 完整视频分析页：
  - 文件选择+上传（格式校验+.mp4/.avi/.mov/.mkv）
  - 视频首帧预览
  - Canvas ROI矩形绘制（鼠标拖拽）
  - 分析进度轮询+事件列表展示

## 明日计划（6月28日）

- 完善ROI交互（调整大小、触摸支持）
- 报警中心页 `AlarmCenterView.vue`
- 历史事件页 `HistoryView.vue`
- 结果视频回放组件
- 对接事件接口

## 技术笔记

- 深色主题色板：#07111f(背景) #101f33(卡片) #0b1728(侧栏) #1e3a5f(边框)
- 强调色：#00d8ff(cyan) #00ffb2(成功绿) #ff4d4f(失败红)
- 响应拦截器自动解包：`{code:200, data:...}` → 只返回data，非200抛异常
- 所有页面使用 `<script setup>` + Composition API
- 无状态管理库，用localStorage存token + 组件内ref
