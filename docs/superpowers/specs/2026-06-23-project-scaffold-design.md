# 高空抛物监测系统项目框架设计

## 1. 目标

搭建一个可运行、可分工、可逐步扩展的最小项目框架，使五名成员能立即按前端、后端、算法、测试和集成方向并行开发。

## 2. 设计原则

- 只搭建当前确定的技术栈和模块边界，不提前实现完整业务。
- 前端、后端、算法模块独立，使用明确接口通信。
- 首次运行只需完成前端页面启动、后端健康检查和基础测试。
- 数据集、模型、视频、运行数据库不提交Git。
- Windows作为当前开发和答辩环境。

## 3. 技术栈

| 模块 | 技术 |
|---|---|
| 前端 | Vue 3、Vite、JavaScript |
| 后端 | Python、FastAPI、Uvicorn |
| 数据库 | SQLite |
| 算法 | Python、YOLO、DeepSORT、OpenCV |
| 测试 | Pytest、FastAPI TestClient |
| 配置 | `.env.example`与环境变量 |

前端首版不引入Element Plus和ECharts，待具体页面开发时按需添加，避免框架阶段产生无用依赖。

## 4. 目录结构

```text
project/
├─ frontend/
│  ├─ src/
│  │  ├─ api/              # 后端接口封装
│  │  ├─ components/       # 通用组件
│  │  ├─ views/            # 页面
│  │  ├─ App.vue
│  │  └─ main.js
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ backend/
│  ├─ app/
│  │  ├─ api/              # API路由
│  │  ├─ core/             # 配置
│  │  ├─ models/           # 数据模型
│  │  ├─ services/         # 业务服务
│  │  └─ main.py
│  ├─ data/                # SQLite运行目录，不提交数据库文件
│  └─ requirements.txt
├─ algorithm/
│  ├─ detection/           # YOLO检测
│  ├─ tracking/            # DeepSORT跟踪
│  ├─ behavior/            # 轨迹行为判定
│  └─ pipeline.py          # 算法统一入口
├─ tests/
│  └─ backend/             # 后端测试
├─ scripts/
│  ├─ start-backend.ps1
│  └─ start-frontend.ps1
├─ docs/
│  ├─ architecture.md
│  └─ development-guide.md
├─ .env.example
├─ .gitignore
├─ README.md
└─ CLAUDE.md
```

空业务目录使用`.gitkeep`保留，后续由对应负责人填充。

## 5. 初始可运行能力

### 5.1 后端

- 提供`GET /api/health`接口。
- 返回服务状态、项目名称和API版本。
- 配置允许通过环境变量覆盖。
- 提供自动API文档`/docs`。

响应示例：

```json
{
  "status": "ok",
  "service": "High-altitude Object Throwing Monitoring System",
  "version": "0.1.0"
}
```

### 5.2 前端

- 显示项目名称和“系统框架运行正常”。
- 请求后端健康检查接口。
- 明确显示后端在线或离线状态。
- 仅使用基础CSS，不提前设计完整管理平台。

### 5.3 算法

- 只定义统一流水线入口和结果数据结构。
- 初始实现返回“未加载模型”的明确状态。
- 不引入YOLO、DeepSORT和CUDA依赖。
- 后续算法开发不影响前后端目录。

## 6. 模块接口

算法流水线后续统一接收：

```text
视频路径或摄像头编号 + ROI + 检测参数
```

统一输出：

```text
任务状态 + 当前帧 + 检测结果 + 跟踪结果 + 事件结果
```

框架阶段仅保留Python接口边界，不实现视频处理。

前端统一通过`frontend/src/api/`访问后端，页面中不直接散落请求地址。

## 7. 配置与运行数据

`.env.example`包含：

- 后端主机和端口。
- 前端访问的API地址。
- SQLite数据库路径。
- 上传、输出和模型目录。

运行时目录由后续业务模块创建。数据集、模型、上传视频、输出视频、日志和数据库均由`.gitignore`排除。

## 8. 测试与验收

框架完成必须满足：

1. 后端可启动，访问`/api/health`返回HTTP 200。
2. 后端自动文档可访问。
3. Pytest健康检查测试通过。
4. 前端依赖安装后可启动。
5. 前端能显示后端连接状态。
6. 所有Python文件可通过语法检查。
7. Git状态中不包含缓存、依赖、数据库或敏感配置。
8. README和开发指南包含零基础启动步骤。

## 9. 协作边界

| 目录 | 主要负责人 |
|---|---|
| `frontend/` | 刘康 |
| `backend/` | 陈磊 |
| `algorithm/` | 石义焌 |
| `tests/` | 杨锦辉 |
| `scripts/`、根配置、集成 | 罗龙飞 |

跨目录修改前需通知目录负责人；所有功能通过独立分支和Pull Request合并到`dev`。

## 10. 暂不包含

- 登录、视频上传、实时监控等正式页面。
- 数据库表和业务CRUD。
- YOLO模型加载和推理。
- DeepSORT跟踪和行为规则。
- 报警、事件存储和视频回放。
- Docker、Linux和边缘设备部署。

这些功能应在框架稳定后按模块分别设计和实现。
