# 高空抛物监测系统

面向生产实习答辩的 AI 原型系统，完成**视频输入 → 目标检测与跟踪 → 行为判定 → 实时报警 → 事件存储与回放**的演示闭环。

核心目标：2026年7月3日前交付可演示、可测试、可说明的完整系统。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3, Vite, Element Plus, ECharts, Axios |
| 后端 | Python 3.13+, FastAPI, Uvicorn, SQLite |
| 算法 | YOLOv11, ONNX Runtime, OpenCV, DeepSORT, scipy |
| 测试 | pytest, pytest-cov, Playwright |

## 项目结构

```
├── algorithm/                    # 算法流水线
│   ├── pipeline.py               #   主入口 run_video_analysis()
│   ├── detection/detector.py     #   YOLOv11 ONNX检测器
│   ├── tracking/tracker.py       #   DeepSORT目标跟踪
│   └── behavior/behavior.py      #   6条件抛物行为判定
├── backend/app/                  # FastAPI后端
│   ├── main.py                   #   应用入口、CORS、路由注册、lifespan
│   ├── api/                      #   10个路由模块（REST端点）
│   │   ├── auth.py               #     POST /api/auth/login
│   │   ├── health.py             #     GET  /api/health
│   │   ├── system.py             #     GET  /api/system/status
│   │   ├── events.py             #     GET/PATCH /api/events
│   │   ├── videos.py             #     POST/GET /api/videos
│   │   ├── files.py              #     GET  /api/files
│   │   ├── statistics.py         #     GET  /api/statistics/overview
│   │   ├── settings.py           #     GET/PUT /api/settings
│   │   └── camera.py             #     POST/GET camera + SSE status stream
│   ├── core/                     #   基础设施
│   │   ├── auth.py               #     Token生成/验证/过期
│   │   ├── config.py             #     pydantic-settings配置
│   │   ├── database.py           #     SQLite建表+连接管理
│   │   └── security.py           #     文件路径白名单校验
│   ├── models/schemas.py         #   Pydantic请求/响应模型
│   └── services/                 #   业务逻辑层
│       ├── event_service.py      #     事件CRUD+批量写入
│       ├── task_service.py       #     任务管理+后台分析线程
│       ├── video_service.py      #     视频文件保存
│       ├── camera_service.py     #     OpenCV摄像头+AI会话
│       ├── camera_ai.py          #     实时AI帧处理会话
│       ├── settings_service.py   #     系统参数读写+校验
│       └── statistics_service.py #     仪表板6维统计聚合
├── frontend/src/                 # Vue 3前端
│   ├── App.vue                   #   根组件
│   ├── main.js                   #   入口（Vue/ECharts/ElementPlus注册）
│   ├── router/index.js           #   路由守卫+页面映射
│   ├── api/                      #   10个Axios请求模块
│   ├── components/MainLayout.vue #   侧边栏+顶栏布局
│   ├── views/                    #   8个页面组件
│   │   ├── LoginView.vue         #     登录页
│   │   ├── HomeView.vue          #     首页（主演示闭环流程图）
│   │   ├── DashboardView.vue     #     仪表板（统计卡片+趋势图）
│   │   ├── VideoAnalysisView.vue #     视频分析（上传→配置→ROI→结果）
│   │   ├── MonitorView.vue       #     实时监控（摄像头MJPEG+AI标注）
│   │   ├── AlarmCenterView.vue   #     报警中心（事件列表+分页+确认/误报）
│   │   ├── HistoryView.vue       #     历史回放（筛选+分页+轨迹数据）
│   │   └── SettingsView.vue      #     参数设置（7项算法阈值）
│   └── utils/dashboard.js        #   仪表板辅助函数
├── scripts/                      # 工具脚本
│   ├── start-backend.ps1         #   启动后端(.venv)
│   ├── start-backend-conda.ps1   #   启动后端(Conda, 有GPU)
│   ├── start-frontend.ps1        #   启动前端开发服务器
│   ├── pipeline_cli.py           #   算法CLI入口（子进程调用）
│   ├── train.py                  #   YOLO训练脚本
│   ├── export_onnx.py            #   PyTorch→ONNX导出
│   ├── evaluate.py               #   模型评估
│   ├── test_model.py             #   模型快速测试
│   ├── prepare_dataset.py        #   数据集准备（LabelImg→YOLO格式）
│   ├── annotate.py               #   图像标注辅助
│   ├── check_yolo_env.py         #   算法环境检查
│   └── record_demo.py            #   演示视频录制
├── tests/                        # 测试
│   ├── backend/                  #   pytest后端测试（148 tests）
│   ├── algorithm/                #   算法单元测试（7 tests）
│   ├── frontend/                 #   Playwright E2E（20 tests）
│   └── integration/              #   集成测试用例+记录
├── config/default.yaml           # 算法阈值默认值
├── models/                       # 模型权重（best.pt, best.onnx）
├── data/                         # 数据集+演示视频（demo.mp4）
├── docs/                         # 项目文档（架构/API设计/计划/报告）
├── CLAUDE.md                     # AI编码规范
└── AGENTS.md                     # 项目记忆（目标/技术决策）
```

## 处理逻辑

### 核心数据流

```
视频输入 → 目标检测 → 目标跟踪 → 行为判定 → 报警事件 → 结果视频
  │           │          │          │          │           │
  │      YOLOv11    DeepSORT   6条件判断   数据库存储   MJPEG叠加
  │      ONNX推理   IOU匹配    线性回归    快照截图     检测框/轨迹/ROI
  └──────────────────────────────────────────────────────────┘
                        后台线程异步执行
```

### 算法流水线（algorithm/pipeline.py）

**1. 检测（detection/detector.py）**
- 使用 YOLOv11 ONNX 模型对每帧进行推理
- 输出检测框列表：`[{frame_id, bbox_x, bbox_y, bbox_width, bbox_height, confidence, class_name}]`
- ROI 过滤：仅保留中心点在 ROI 矩形内的检测结果

**2. 跟踪（tracking/tracker.py）**
- DeepSORT 多目标跟踪器，为每个检测分配 track_id
- 维护目标轨迹：`[{frame_id, time, x, y}]` 时间序列
- 区分 confirmed / tentative / deleted 三种状态
- 输出跟踪结果：`[{frame_id, track_id, bbox, center, confidence, status}]`

**3. 行为判定（behavior/behavior.py）**
- 六条件联合判断是否为抛物事件：

| 条件 | 判定方式 | 可配置参数 |
|------|---------|-----------|
| ① 轨迹足够长 | 帧数 ≥ 阈值 | `min_track_frames` |
| ② 整体向下运动 | 线性回归斜率 ≥ 阈值 | `downward_ratio` |
| ③ 累计垂直位移 | y位移 ≥ 阈值(像素) | `min_vertical_distance` |
| ④ ROI内轨迹占比 | 轨迹点在ROI内比例 ≥ 阈值 | `roi_required_ratio` |
| ⑤ 报警冷却 | 同一track_id距上次报警 ≥ 阈值 | `alarm_cooldown_seconds` |
| ⑥ 检测置信度 | YOLO检测阶段已过滤 | `detect_confidence` |

- 全部满足 → 触发事件，返回 EventInfo
- 事件包含：track_id, timestamp, confidence, trajectory, snapshot_path

**4. 结果输出**
- 逐帧绘制标注：检测框（绿）、ROI（蓝）、轨迹线、track_id标签、事件高亮（红）
- 写入 result.mp4（H.264编码）
- 事件触发帧保存快照 JPG
- 输出 progress.json 供前端轮询进度

### 后端处理链（backend/）

```
HTTP请求 → FastAPI路由 → Depends(auth) → Service层 → SQLite
                │              │
          统一响应格式    Token鉴权/过期
        {code, data, message}
```

**视频分析流程（完整链路）：**
```
POST /api/videos/upload  →  保存文件到 uploads/
POST /api/videos/{id}/analyze  →  create_task() + start_analysis()
  └─ 后台线程 _run_analysis()
       ├─ update_task(status="running")
       ├─ subprocess.run(pipeline_cli.py)  →  algorithm.pipeline.run_video_analysis()
       ├─ 解析 JSON 输出
       └─ batch_insert_events/detections/tracks  →  update_task(status="success")
```

**实时监控流程（摄像头模式）：**
```
POST /api/camera/start     →  OpenCV打开摄像头 → 后台帧捕获线程
POST /api/camera/ai/start  →  创建CameraAISession → 逐帧检测/跟踪/行为判定
GET  /api/camera/stream    →  MJPEG流（AI标注帧或原始帧）
GET  /api/camera/status/stream → SSE推送状态（每3秒）
```

### 数据库设计（5表）

| 表 | 关键字段 | 用途 |
|----|---------|------|
| system_settings | id=1单行, detect_confidence, downward_ratio, imgsz等7参数 | 系统参数 |
| video_tasks | source_type(upload/camera), status, roi, result_video_path | 分析任务 |
| events | video_task_id, track_id, confidence, status(unconfirmed/confirmed/false_alarm) | 抛物事件 |
| detection_results | video_task_id, frame_id, bbox, confidence, class_name | 检测结果 |
| tracking_results | video_task_id, frame_id, track_id, bbox, center, status | 跟踪结果 |

### 前端路由与页面流

```
/login              →  LoginView           Token鉴权
/home               →  HomeView            主演示闭环流程图
/dashboard          →  DashboardView       统计卡片+趋势柱状图+最近事件
/video-analysis     →  VideoAnalysisView   上传→配置→ROI绘制→分析进度→结果视频+快照
/monitor            →  MonitorView         摄像头MJPEG+ROI框选+AI开关+实时事件
/alarm-center       →  AlarmCenterView     未确认事件列表+分页+确认/误报操作
/history            →  HistoryView         筛选(状态/时间/置信度)+分页+轨迹数据
/settings           →  SettingsView        7项算法参数调整(带校验范围)
```

路由守卫：未登录自动跳转 `/login`，登录后 Token 存 localStorage 并自动附加到 Axios 请求头。

## 快速启动

**环境要求**: Python 3.10+, Node.js 20+, Git

```powershell
# 1. 后端环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env

# 2. 前端环境
Set-Location frontend
npm install
Set-Location ..
```

**启动**:

```powershell
# 后端（CPU模式）
.\scripts\start-backend.ps1

# 后端（GPU/Conda模式，需要 D:\Soft\Conda 含 torch+ultralytics）
.\scripts\start-backend-conda.ps1

# 前端（新终端）
.\scripts\start-frontend.ps1
```

**访问**:

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:5173 | 前端页面 |
| http://127.0.0.1:8157/api/health | 后端健康检查 |
| http://127.0.0.1:8157/docs | Swagger API文档 |

默认登录：`admin` / `admin123`

## 测试

```powershell
# 全量后端+算法测试（需Conda环境含ultralytics）
KMP_DUPLICATE_LIB_OK=TRUE D:\Soft\Conda\python.exe -m pytest tests/backend/ tests/algorithm/ -v

# 含覆盖率报告
KMP_DUPLICATE_LIB_OK=TRUE D:\Soft\Conda\python.exe -m pytest tests/ --cov=backend --cov=algorithm --cov-report=term-missing

# 仅后端测试（无需ultralytics，使用.venv）
.venv\Scripts\python.exe -m pytest tests/backend/ -v

# 前端E2E
Set-Location tests\frontend
npx playwright test
```

### 测试概况

| 套件 | 位置 | 数量 | 覆盖 |
|------|------|------|------|
| pytest 后端 | tests/backend/ | 148 | API路由/鉴权/数据库/服务层/安全 |
| pytest 算法 | tests/algorithm/ | 7 | 流水线端到端/环境检查/数据集 |
| Playwright | tests/frontend/ | 20 | 登录/首页/视频分析 |
| 集成测试 | tests/integration/ | 25项 | 手动测试用例+记录 |
| **合计** | | **200** | **80%代码覆盖** |

### API端点一览

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/health | 否 | 健康检查 |
| POST | /api/auth/login | 否 | 登录获取Token |
| GET | /api/system/status | 是 | 系统4维状态 |
| GET | /api/events | 是 | 事件列表+筛选+分页 |
| PATCH | /api/events/{id} | 是 | 更新事件状态 |
| POST | /api/videos/upload | 是 | 上传视频文件 |
| GET | /api/videos/{id} | 是 | 查询任务详情 |
| POST | /api/videos/{id}/analyze | 是 | 启动后台分析 |
| GET | /api/files | 否 | 文件服务（快照/视频） |
| GET | /api/statistics/overview | 是 | 仪表板6维统计 |
| GET | /api/settings | 是 | 读取系统参数 |
| PUT | /api/settings | 是 | 更新系统参数 |
| POST | /api/camera/start | 是 | 启动摄像头 |
| POST | /api/camera/stop | 是 | 停止摄像头 |
| GET | /api/camera/stream | 否 | MJPEG视频流 |
| GET | /api/camera/status/stream | 否 | SSE状态推送 |
| POST | /api/camera/ai/start | 是 | 启动实时AI |
| POST | /api/camera/ai/stop | 是 | 停止实时AI |
| GET | /api/camera/ai/status | 是 | AI状态查询 |

统一响应格式：`{code: int, message: str, data: any}`，前端 `request.js` 拦截器自动解包。

## 文档

| 文档 | 说明 |
|------|------|
| [系统架构](docs/architecture.md) | 技术架构与模块关系 |
| [开发指南](docs/development-guide.md) | 环境搭建与开发规范 |
| [算法接口合同](docs/algorithm-interface.md) | pipeline输入输出字段规范 |
| [详细API设计](docs/详细API设计.md) | 全部REST端点设计 |
| [详细需求分析](docs/详细需求分析.md) | 需求文档 |
| [详细开发计划](docs/详细开发计划.md) | 开发排期 |
| [前期规划](docs/高空抛物监测系统-前期规划.md) | 项目早期规划 |
| [推理逻辑说明](docs/推理逻辑说明.md) | 行为判定6条件详解 |
| [设计稿规范](docs/design.md) | UI设计规范 |
| [全链路测试报告](docs/全链路测试报告-2026-06-30.md) | 最新测试报告（2026-06-30） |
| [YOLO训练说明](docs/YOLO训练到系统接入说明.md) | 训练到部署流程 |
| [训练记录](docs/训练记录与参数总结.md) | 训练参数与结果 |
| [GitHub协作指南](docs/GitHub团队协作指南.md) | 团队Git工作流 |
| [每日工作流](docs/daily-workflow.md) | 每日开发流程 |
| [项目进度总结](docs/项目进度与不足总结-2026-06-30.md) | 6/30进度总结 |
| [PPT大纲](docs/ppt-outline-2026-07-03.md) | 答辩PPT大纲 |
