# AGENTS.md

## 项目记忆

### 项目目标

本项目是“高空抛物监测系统”，用于生产实习人工智能方向课程答辩。

核心目标不是工业级部署，而是在 2026年7月3日 前完成一个可演示、可测试、可说明的 AI 原型系统。

主演示闭环：

```text
管理员登录
→ 上传视频
→ 绘制 ROI
→ 创建分析任务
→ YOLOv11 检测
→ DeepSORT 跟踪
→ 轨迹规则判断
→ 报警
→ 事件入库
→ 历史回放
→ 数据看板统计
```

辅演示闭环：

```text
笔记本摄像头
→ 实时画面
→ YOLOv11 检测框
```

最高优先级：上传视频主演示闭环。

## 技术栈

| 类型 | 技术 |
|---|---|
| 开发语言 | Python 3.10、JavaScript |
| 前端 | Vue 3、Vite、Element Plus、ECharts |
| 后端 | FastAPI、Uvicorn |
| 数据库 | SQLite |
| 视频处理 | OpenCV、FFmpeg |
| 目标检测 | YOLOv11 |
| 目标跟踪 | DeepSORT |
| 推理优化 | ONNX Runtime，非阻塞项 |
| 测试 | pytest、前端 build |
| 协作 | Git、GitHub、PR |
| 部署环境 | Windows 笔记本本地部署 |

## 目录结构

```text
backend/                 FastAPI 后端
backend/app/             后端应用代码
algorithm/               算法 Pipeline、检测、跟踪、行为判断
frontend/                Vue 3 前端
frontend/src/            前端页面、组件、API 调用
scripts/                 Windows 启动脚本
tests/                   后端与算法测试
docs/                    架构、开发指南、计划文档
uploads/                 上传视频，本地运行生成，不提交 Git
outputs/                 结果视频，本地运行生成，不提交 Git
events/                  事件截图，本地运行生成，不提交 Git
models/                  模型权重，本地保存，大文件不直接提交 Git
logs/                    日志文件，本地生成，不提交 Git
```

重要文档：

- `详细需求分析.md`
- `详细开发计划.md`
- `详细API设计.md`
- `design.md`
- `刘康6月24日前端路由与页面布局草案.md`
- `罗龙飞负责人任务清单.md`
- `高空抛物监测系统-前期规划.md`
- `GitHub团队协作指南.md`
- `docs/architecture.md`
- `docs/development-guide.md`
- `CLAUDE.md`

## 关键约束

- 只有一个系统用户角色：管理员。
- 管理员账号固定为 `admin/admin123`，不做用户表。
- 主演示使用“上传视频检测”，摄像头只做辅演示。
- 摄像头模式只要求实时画面和 YOLOv11 检测框，不要求报警入库。
- 报警事件状态：`unconfirmed / confirmed / false_alarm`。
- 视频证据保存：事件截图 + 完整结果视频。
- 上传视频任务需要真实进度：`processed_frames / total_frames`。
- ROI 使用前端矩形框：`roi_x / roi_y / roi_width / roi_height`。
- 上传与 ROI 流程：上传先创建任务，ROI 后通过任务分析接口提交。
- 摄像头画面传输方式定为 MJPEG 流。
- 数据库使用 SQLite，不做 MySQL。
- ONNX Runtime 是应该完成项，但失败不阻塞主演示。
- 6月27日完全休息，不安排开发交付。
- 日常开发时间：15:00—22:00，必要时上午加班。
- 主演示机：罗龙飞 RTX3050 4GB。
- 主训练机：石义焌 RTX4060 8GB。
- 备用演示机：陈磊 RTX3050 4GB。

## 当前已完成

- 已完成项目基础框架。
- 已完成 FastAPI 健康检查接口。
- 已完成 Vue 基础状态页。
- 已完成算法 Pipeline 占位接口。
- 已完成 Windows 前后端启动脚本。
- 已完成 README、架构文档、开发指南。
- 已完成 GitHub 团队协作指南。
- 已完成详细需求分析，并补充数据建模、功能建模、模块联系。
- 已完成详细开发计划。
- 已完成罗龙飞负责人任务清单。
- 已完成详细 API 设计。
- 已完成刘康 6月24日 前端路由与页面布局草案。
- 已完成 `design.md` 深色科技风前端视觉设计说明。
- 已生成 Figma 设计稿：
  - 文件名：高空抛物监测系统-深色科技风设计稿
  - 链接：https://www.figma.com/design/z3fOmOnu8lSACcD6RfG5k5
  - 内容：设计说明 + 登录页 + 首页 + 视频分析页 + 报警中心 + 历史事件 + 数据看板 + 参数设置 + 实时监控
- 已确定核心数据表：
  - `video_tasks`
  - `events`
  - `detection_results`
  - `tracking_results`
  - `system_settings`
- 已确定核心接口：
  - `POST /api/auth/login`
  - `GET /api/health`
  - `GET /api/system/status`
  - `POST /api/videos/upload`
  - `POST /api/tasks/{task_id}/analyze`
  - `GET /api/tasks/{task_id}`
  - `GET /api/events`
  - `GET /api/events/{event_id}`
  - `PATCH /api/events/{event_id}/status`
  - `GET /api/statistics/overview`
  - `GET /api/settings`
  - `PUT /api/settings`
  - `GET /api/files`
  - `POST /api/camera/start`
  - `POST /api/camera/stop`
  - `GET /api/camera/status`
  - `GET /api/camera/stream`

## 当前问题

当前代码仍主要是项目框架，业务功能尚未完整实现。

待完成重点：

- SQLite 业务表初始化。
- 登录接口和 token 校验。
- 视频上传与后台任务。
- ROI 提交与分析任务启动。
- YOLOv11 推理接入。
- DeepSORT 跟踪接入。
- 轨迹规则判断。
- 事件入库。
- 结果视频生成。
- 报警中心。
- 历史事件回放。
- 数据看板。
- 摄像头 MJPEG 流。
- 测试报告和 PPT 证据材料。

若时间紧，优先保：

```text
上传视频 → ROI → 检测 → 跟踪 → 报警 → 入库 → 回放
```

## 常用命令

### 后端环境

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

### 启动后端

```powershell
.\scripts\start-backend.ps1
```

或：

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 启动前端

```powershell
.\scripts\start-frontend.ps1
```

或：

```powershell
Set-Location frontend
npm install
npm run dev
```

### 访问地址

```text
前端：http://127.0.0.1:5173
后端健康检查：http://127.0.0.1:8000/api/health
后端 API 文档：http://127.0.0.1:8000/docs
Figma：https://www.figma.com/design/z3fOmOnu8lSACcD6RfG5k5
```

### 测试

```powershell
python -m pytest -v
python -m compileall backend algorithm tests
Set-Location frontend
npm run build
```

若 pytest 受全局插件影响：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -v
```

### Git 协作

```powershell
git switch dev
git pull origin dev
git switch -c feature/姓名-任务
git status
git add <本次修改文件>
git commit -m "类型: 描述"
git push -u origin feature/姓名-任务
```

提交类型：

```text
feat: 新功能
fix: 修复
docs: 文档
test: 测试
chore: 工程配置
```

## 禁止事项

- 禁止直接修改 `main`。
- 禁止绕过 PR 直接合并重要代码。
- 禁止删除他人代码或未确认的文件。
- 禁止提交 `.env`、虚拟环境、缓存、上传视频、结果视频、日志、大模型权重。
- 禁止把摄像头辅演示当作主演示依赖。
- 禁止承诺工业级准确率或真实边缘设备部署。
- 禁止把“人为抛出”和“自然掉落”做精确区分，本项目统一称为“疑似高空抛物事件”。
- 禁止引入复杂中间件，当前不使用 Celery、Redis、MySQL。
- 禁止主动重构无关代码。
- 禁止为了美化大改架构。
- 禁止写无法验证的功能描述。
- 禁止修改接口字段后不通知前后端和测试负责人。
- 禁止最后一天才集成；至少每两天端到端集成一次。

## Agent 工作规则

- 编码前先读 `CLAUDE.md`。
- 文档变更优先保持与 `详细需求分析.md`、`详细开发计划.md`、`详细API设计.md` 一致。
- 代码变更必须小步、可验证。
- 修改前先确认当前分支和工作区状态。
- 只做用户要求的任务，不主动扩展范围。
- 发现文档和代码矛盾时，先指出矛盾，再按需求分析和开发计划修正。
- 完成后说明修改文件和验证结果。
