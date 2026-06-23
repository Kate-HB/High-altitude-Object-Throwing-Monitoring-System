# 开发指南

## 1. 环境要求

Windows 10/11，建议安装：

- Python 3.10 或更高版本。
- Node.js 20 LTS 或更高版本，附带 npm。
- Git 2.40 或更高版本。
- VS Code 或 PyCharm。

在 PowerShell 检查：

```powershell
python --version
node --version
npm --version
git --version
```

若系统只有 `py` 命令，可在下列 Python 命令中将 `python` 替换为 `py`；项目启动脚本目前要求 `python` 命令可用。

## 2. 获取代码

```powershell
git clone <仓库地址>
Set-Location "High-altitude-Object-Throwing-Monitoring-System"
```

已有本地仓库时：

```powershell
git switch dev
git pull origin dev
```

## 3. 配置后端

在项目根目录执行：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

虚拟环境激活后，命令行前通常显示 `(.venv)`。`.env` 是个人配置，不提交 Git。

启动后端：

```powershell
.\scripts\start-backend.ps1
```

也可直接启动：

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

验证地址：

- 健康检查：<http://127.0.0.1:8000/api/health>
- API 文档：<http://127.0.0.1:8000/docs>

## 4. 配置前端

新开一个 PowerShell，进入项目根目录：

```powershell
Set-Location frontend
npm install
npm run dev
```

也可在项目根目录运行：

```powershell
.\scripts\start-frontend.ps1
```

访问 <http://127.0.0.1:5173>。前后端均启动时，页面应显示“后端服务在线”。

前端读取项目根目录 `.env` 中的 `VITE_API_BASE_URL`。修改环境变量后需重启前端开发服务器。

## 5. 测试与构建

在项目根目录运行全部 Python 测试：

```powershell
python -m pytest -v
```

分别运行：

```powershell
python -m pytest tests\backend\test_health.py -v
python -m pytest tests\algorithm\test_pipeline.py -v
```

检查 Python 语法：

```powershell
python -m compileall backend algorithm tests
```

构建前端：

```powershell
Set-Location frontend
npm run build
```

构建结果生成在 `frontend/dist/`，该目录不提交 Git。

## 6. Git 最短协作流程

每项任务从最新 `dev` 创建独立分支：

```powershell
git switch dev
git pull origin dev
git switch -c feature/姓名-任务
```

完成一个可验证的小功能后：

```powershell
git status
git add <本次修改的文件>
git commit -m "类型: 简短描述"
git push -u origin feature/姓名-任务
```

在 GitHub 创建 `个人分支 → dev` 的 Pull Request，填写改动、测试结果和截图。审核通过后合并；禁止直接向 `main` 或 `dev` 推送。

常用提交类型：

- `feat`：新增功能。
- `fix`：修复问题。
- `docs`：文档变更。
- `test`：测试变更。
- `chore`：工程配置或辅助任务。

## 7. 常见故障

### PowerShell 禁止运行脚本

仅对当前窗口临时放行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### `python` 命令不存在

重新安装 Python 并勾选“Add Python to PATH”，或先用 `py` 替代 `python`。启动脚本依赖 `python`，需确保其最终可用。

### Python 模块不存在

确认已激活 `.venv`，并重新安装：

```powershell
python -m pip install -r backend\requirements.txt
```

### npm 或前端依赖不存在

确认 Node.js 已安装，然后执行：

```powershell
Set-Location frontend
npm install
```

### 8000 或 5173 端口被占用

查找占用进程：

```powershell
Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue |
  Select-Object LocalPort,OwningProcess
```

确认进程无用后，由进程所有者关闭。不要随意结束不认识的系统进程。

### 页面显示“后端服务离线”

依次检查：

1. 后端终端是否报错。
2. <http://127.0.0.1:8000/api/health> 是否可访问。
3. 根目录 `.env` 的 `VITE_API_BASE_URL` 是否为 `http://127.0.0.1:8000/api`。
4. 修改 `.env` 后是否重启前端。

### pytest 出现与本项目无关的全局插件冲突

仅在确认报错来自全局 pytest 插件时，在当前 PowerShell 临时禁用自动加载，再执行测试：

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -v
```

关闭当前 PowerShell 后该环境变量失效。正常情况下不要设置此变量。

### Git 合并冲突

不要删除他人代码或强制推送。停止合并，保留终端报错和冲突文件，由罗龙飞协调相关负责人共同处理。
