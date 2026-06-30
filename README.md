# 高空抛物监测系统

面向生产实习答辩的 Web 监测平台。目标是完成"视频输入、目标检测与跟踪、行为判定、实时报警、事件存储与回放"的演示闭环。

## 当前能力

- FastAPI 后端：健康检查、Token鉴权、视频上传、任务管理、后台分析线程、事件CRUD、文件服务、统计接口、参数读写、摄像头MJPEG流
- SQLite 数据库：5张业务表（video_tasks, events, detection_results, tracking_results, system_settings）
- Vue 3 前端：登录、首页仪表板、视频分析（上传+ROI+进度）、报警中心、历史回放、数据看板（ECharts）、参数设置、实时监控（摄像头）
- 算法流水线：YOLOv11检测 → IOU跟踪 → 6条件行为判断 → 结果视频（检测框+轨迹+ROI叠加）
- ONNX推理：`models/best.onnx` (10.3 MB, opset=17)，GPU推理验证通过
- 82个pytest后端测试 + 20个Playwright前端E2E测试 + 25项手动集成测试
- 统一响应格式 `{code, data, message}`，前端拦截器自动解包

## 技术栈

- 前端：Vue 3、Vite、Element Plus、ECharts、Axios
- 后端：Python 3.13+、FastAPI、Uvicorn、SQLite
- 算法：YOLOv11、OpenCV、IOU Tracker、ONNX Runtime
- 测试：pytest、Playwright

## 目录

```text
algorithm/               算法流水线及检测、跟踪、行为判定
backend/                 FastAPI应用、业务服务、数据模型
frontend/                Vue 3前端
scripts/                 工具脚本（启动/OONX导出/评估/演示录制/模型测试）
config/                  算法阈值配置
models/                  模型权重（best.pt + best.onnx）
data/                    数据集和演示视频
tests/
  backend/               pytest后端测试 (82 tests)
  frontend/              Playwright E2E测试 (20 tests)
  algorithm/             算法单元测试
  integration/           集成测试（手动测试记录、用例表、问题清单）
docs/                    架构和开发文档
memory/                  角色记忆
```

## 五分钟启动

要求安装 Python 3.10+、Node.js 20+ 和 Git。

在项目根目录执行：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
Set-Location frontend
npm install
Set-Location ..
```

启动后端：

```powershell
.\scripts\start-backend.ps1
```

新开 PowerShell，在项目根目录启动前端：

```powershell
.\scripts\start-frontend.ps1
```

访问：

- 前端：<http://127.0.0.1:5173>
- 后端健康检查：<http://127.0.0.1:8000/api/health>
- 后端 API 文档：<http://127.0.0.1:8000/docs>

## 测试

```powershell
# 后端自动化测试
python -m pytest -v

# Python语法编译检查
python -m compileall backend algorithm tests

# 前端构建检查
Set-Location frontend
npm run build

# 前端E2E测试
Set-Location ..\tests\frontend
npx playwright test
```

| 测试套件 | 位置 | 数量 | 类型 |
|---|---|---|---|
| pytest | `tests/backend/` | 82 | 接口+鉴权+数据库 |
| Playwright | `tests/frontend/` | 20 | 登录+首页+视频分析 |
| 集成测试 | `tests/integration/` | 25 | 手动+curl+DB验证 |

## 文档

- [系统架构](docs/architecture.md)
- [开发指南](docs/development-guide.md)
- [每日工作流](docs/daily-workflow.md)
- [算法接口合同](docs/algorithm-interface.md)
- [设计稿规范](design.md)
- [GitHub团队协作指南](GitHub团队协作指南.md)
- [前期规划](高空抛物监测系统-前期规划.md)
