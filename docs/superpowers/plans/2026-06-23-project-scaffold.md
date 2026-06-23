# Project Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建可运行、可测试、适合五人并行协作的Vue 3、FastAPI和算法接口最小项目框架。

**Architecture:** 前端通过独立API模块访问FastAPI；后端提供配置和健康检查；算法目录暴露不依赖模型的统一流水线接口。框架不实现业务功能，只验证模块边界、启动方式和协作目录。

**Tech Stack:** Vue 3、Vite、JavaScript、Python 3.10+、FastAPI、Uvicorn、Pydantic Settings、Pytest

---

## 文件结构

将创建或修改：

- `.gitignore`：排除依赖、环境变量、模型、视频和运行数据。
- `.env.example`：统一环境变量样例。
- `backend/requirements.txt`：后端最小依赖。
- `backend/app/core/config.py`：读取后端配置。
- `backend/app/api/health.py`：健康检查路由。
- `backend/app/main.py`：FastAPI应用入口和CORS配置。
- `tests/backend/test_health.py`：健康检查接口测试。
- `algorithm/pipeline.py`：算法统一入口和结果结构。
- `tests/algorithm/test_pipeline.py`：算法占位行为测试。
- `frontend/package.json`：前端依赖和命令。
- `frontend/vite.config.js`：Vite开发配置。
- `frontend/index.html`：前端入口HTML。
- `frontend/src/main.js`：Vue启动入口。
- `frontend/src/App.vue`：框架状态页面。
- `frontend/src/api/health.js`：后端健康检查请求。
- `frontend/src/assets/main.css`：基础样式。
- `scripts/start-backend.ps1`：后端启动脚本。
- `scripts/start-frontend.ps1`：前端启动脚本。
- `docs/architecture.md`：架构和模块边界。
- `docs/development-guide.md`：零基础开发与启动说明。
- `README.md`：项目总览和快速开始。

### Task 1：基础配置与目录

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/models/.gitkeep`
- Create: `backend/app/services/.gitkeep`
- Create: `backend/data/.gitkeep`
- Create: `algorithm/__init__.py`
- Create: `algorithm/detection/.gitkeep`
- Create: `algorithm/tracking/.gitkeep`
- Create: `algorithm/behavior/.gitkeep`
- Create: `frontend/src/components/.gitkeep`
- Create: `frontend/src/views/.gitkeep`

- [ ] **Step 1：创建目录和包标记**

使用`New-Item -ItemType Directory`创建目录，使用`apply_patch`创建文件。

- [ ] **Step 2：写入`.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
node_modules/
frontend/dist/
.env
.env.*
!.env.example
data/
datasets/
uploads/
outputs/
events/
logs/
*.db
*.sqlite
*.sqlite3
*.pt
*.pth
*.onnx
*.engine
*.mp4
*.avi
*.mov
*.mkv
.idea/
.vscode/
.DS_Store
Thumbs.db
```

- [ ] **Step 3：写入`.env.example`**

```dotenv
APP_NAME=High-altitude Object Throwing Monitoring System
APP_VERSION=0.1.0
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_API_BASE_URL=http://127.0.0.1:8000/api
DATABASE_PATH=backend/data/app.db
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MODEL_DIR=models
```

- [ ] **Step 4：检查忽略规则**

Run: `git status --short`

Expected: 只显示计划创建的源码、配置和文档，不显示缓存、数据库、模型或媒体文件。

- [ ] **Step 5：提交**

```bash
git add .gitignore .env.example backend algorithm frontend
git commit -m "chore: create project directory structure"
```

### Task 2：后端健康检查

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/core/config.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/main.py`
- Create: `tests/backend/test_health.py`

- [ ] **Step 1：先写失败测试**

```python
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_returns_service_metadata():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "High-altitude Object Throwing Monitoring System",
        "version": "0.1.0",
    }
```

- [ ] **Step 2：运行测试并确认失败**

Run: `python -m pytest tests/backend/test_health.py -v`

Expected: FAIL，提示`backend.app.main`不存在。

- [ ] **Step 3：写入依赖**

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.34,<1.0
pydantic-settings>=2.7,<3.0
httpx>=0.28,<1.0
pytest>=8.3,<9.0
```

- [ ] **Step 4：实现配置**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "High-altitude Object Throwing Monitoring System"
    app_version: str = "0.1.0"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5：实现健康检查**

```python
from fastapi import APIRouter

from backend.app.core.config import get_settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }
```

- [ ] **Step 6：实现应用入口**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
```

- [ ] **Step 7：运行测试并确认通过**

Run: `python -m pytest tests/backend/test_health.py -v`

Expected: `1 passed`

- [ ] **Step 8：提交**

```bash
git add backend tests/backend
git commit -m "feat: add backend health check"
```

### Task 3：算法统一入口

**Files:**
- Create: `algorithm/pipeline.py`
- Create: `tests/algorithm/test_pipeline.py`

- [ ] **Step 1：先写失败测试**

```python
from algorithm.pipeline import AnalysisPipeline, PipelineResult


def test_pipeline_reports_model_not_loaded():
    result = AnalysisPipeline().analyze("demo.mp4")

    assert result == PipelineResult(
        status="not_ready",
        source="demo.mp4",
        message="Detection model is not loaded",
        detections=[],
        tracks=[],
        events=[],
    )
```

- [ ] **Step 2：运行测试并确认失败**

Run: `python -m pytest tests/algorithm/test_pipeline.py -v`

Expected: FAIL，提示`algorithm.pipeline`不存在。

- [ ] **Step 3：实现最小算法接口**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    status: str
    source: str
    message: str
    detections: list[dict[str, Any]] = field(default_factory=list)
    tracks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)


class AnalysisPipeline:
    def analyze(self, source: str | Path) -> PipelineResult:
        return PipelineResult(
            status="not_ready",
            source=str(source),
            message="Detection model is not loaded",
        )
```

- [ ] **Step 4：运行测试并确认通过**

Run: `python -m pytest tests/algorithm/test_pipeline.py -v`

Expected: `1 passed`

- [ ] **Step 5：提交**

```bash
git add algorithm tests/algorithm
git commit -m "feat: define algorithm pipeline interface"
```

### Task 4：前端状态页面

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/health.js`
- Create: `frontend/src/assets/main.css`

- [ ] **Step 1：写入前端依赖**

```json
{
  "name": "high-altitude-monitor-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2：配置Vite**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
  },
})
```

- [ ] **Step 3：实现健康请求**

```javascript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`)
  }
  return response.json()
}
```

- [ ] **Step 4：实现Vue入口和状态页**

`main.js`：

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'

createApp(App).mount('#app')
```

`App.vue`：

```vue
<script setup>
import { onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'

const status = ref('正在连接后端…')
const online = ref(false)

onMounted(async () => {
  try {
    const result = await fetchHealth()
    online.value = result.status === 'ok'
    status.value = online.value ? '后端服务在线' : '后端状态异常'
  } catch {
    status.value = '后端服务离线'
  }
})
</script>

<template>
  <main class="shell">
    <section class="status-card">
      <p class="eyebrow">AI PRODUCTION PRACTICE</p>
      <h1>高空抛物监测系统</h1>
      <p>系统框架运行正常</p>
      <div class="status" :class="{ online }">
        <span class="status-dot"></span>
        {{ status }}
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 5：写入基础样式和HTML入口**

样式只包含居中布局、状态卡片和在线/离线颜色，不实现正式管理平台。

- [ ] **Step 6：安装并构建**

Run: `npm install`

Workdir: `frontend`

Expected: 依赖安装成功。

Run: `npm run build`

Workdir: `frontend`

Expected: Vite构建成功并生成`frontend/dist/`。

- [ ] **Step 7：提交**

```bash
git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/vite.config.js frontend/src
git commit -m "feat: add frontend service status page"
```

### Task 5：Windows启动脚本

**Files:**
- Create: `scripts/start-backend.ps1`
- Create: `scripts/start-frontend.ps1`

- [ ] **Step 1：实现后端启动脚本**

```powershell
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- [ ] **Step 2：实现前端启动脚本**

```powershell
$ErrorActionPreference = "Stop"
$FrontendDir = Join-Path (Split-Path -Parent $PSScriptRoot) "frontend"
Set-Location $FrontendDir
npm run dev
```

- [ ] **Step 3：检查PowerShell语法**

Run:

```powershell
[System.Management.Automation.Language.Parser]::ParseFile(
  "scripts/start-backend.ps1",
  [ref]$null,
  [ref]$null
)
```

对两个脚本执行，Expected: 无语法错误。

- [ ] **Step 4：提交**

```bash
git add scripts
git commit -m "chore: add Windows startup scripts"
```

### Task 6：架构与开发文档

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/development-guide.md`
- Modify: `README.md`

- [ ] **Step 1：编写架构文档**

必须说明：

- 前端、后端、算法和SQLite职责。
- `视频源 → 后端任务 → 算法流水线 → 事件结果 → 前端展示`数据流。
- 五人目录责任。
- 当前框架边界和后续模块。

- [ ] **Step 2：编写开发指南**

必须提供：

- Python、Node.js和Git版本要求。
- 克隆、虚拟环境、依赖安装命令。
- 前后端启动命令。
- 测试和构建命令。
- 分支、提交和PR最短流程。
- 常见端口占用、依赖缺失和后端离线处理。

- [ ] **Step 3：更新README**

README包含：

- 项目简介。
- 当前能力。
- 技术栈。
- 目录结构。
- 五分钟快速启动。
- 测试命令。
- 文档链接。

- [ ] **Step 4：检查文档命令和路径**

逐条核对路径存在，命令与实际文件一致。

- [ ] **Step 5：提交**

```bash
git add README.md docs/architecture.md docs/development-guide.md
git commit -m "docs: add scaffold development guides"
```

### Task 7：完整验证

**Files:**
- Verify only

- [ ] **Step 1：安装后端依赖**

Run: `python -m pip install -r backend/requirements.txt`

Expected: 安装成功。

- [ ] **Step 2：运行全部Python测试**

Run: `python -m pytest -v`

Expected: `2 passed`

- [ ] **Step 3：检查Python语法**

Run: `python -m compileall backend algorithm tests`

Expected: 无语法错误。

- [ ] **Step 4：构建前端**

Run: `npm run build`

Workdir: `frontend`

Expected: 构建成功。

- [ ] **Step 5：启动后端并验证接口**

Run: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`

验证：

```text
GET http://127.0.0.1:8000/api/health
GET http://127.0.0.1:8000/docs
```

Expected: 健康检查HTTP 200，API文档可访问。

- [ ] **Step 6：启动前端并验证页面**

Run: `npm run dev`

Workdir: `frontend`

验证：

```text
http://127.0.0.1:5173
```

Expected: 显示项目名称、“系统框架运行正常”和“后端服务在线”。

- [ ] **Step 7：检查Git状态**

Run: `git status --short`

Expected: 不包含`node_modules`、`dist`、缓存、模型、视频或数据库。

- [ ] **Step 8：最终提交**

如验证产生必要修正：

```bash
git add 具体修正文件
git commit -m "fix: complete scaffold verification"
```
