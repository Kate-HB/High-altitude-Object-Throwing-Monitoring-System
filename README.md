# 高空抛物监测系统

面向生产实习答辩的 Web 监测平台。目标是完成“视频输入、目标检测与跟踪、行为判定、实时报警、事件存储与回放”的演示闭环。

## 当前能力

- FastAPI 健康检查接口：`GET /api/health`。
- Vue 3 服务状态页，可显示后端在线或离线。
- 算法统一占位接口 `AnalysisPipeline`。
- 后端和算法基础测试。
- Windows 前后端启动脚本。

当前代码是项目框架，尚未实现视频分析、YOLO、DeepSORT、SQLite业务表、报警和回放。

## 技术栈

- 前端：Vue 3、Vite、JavaScript。
- 后端：Python 3.10+、FastAPI、Uvicorn。
- 算法：后续接入 YOLO、OpenCV、DeepSORT、ONNX Runtime。
- 数据：后续使用 SQLite 和本地文件存储。
- 测试：pytest。

## 目录

```text
algorithm/               算法流水线及检测、跟踪、行为判定
backend/                 FastAPI应用、业务服务、数据模型
frontend/                Vue 3前端
scripts/                 Windows启动脚本
tests/                   后端与算法测试
docs/                    架构和开发文档
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
python -m pytest -v
python -m compileall backend algorithm tests
Set-Location frontend
npm run build
```

## 文档

- [系统架构](docs/architecture.md)
- [开发指南](docs/development-guide.md)
- [GitHub团队协作指南](GitHub团队协作指南.md)
- [前期规划](高空抛物监测系统-前期规划.md)
