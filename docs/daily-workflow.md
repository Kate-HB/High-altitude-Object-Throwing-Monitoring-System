# 每日工作流

## 1. 触发方式

用户说"开始今天的工作"或"开始X月X日的工作"，Claude开始执行第一个角色（陈磊）。

用户也可以单独说"完成陈磊X月X日的任务"来只执行某一个角色。

**重要变更（6/26起）**：每个角色完成后Claude自动停止，等待用户手动确认。用户说"继续"才开始下一角色。见第2节。

## 2. 执行顺序（严格串行）

```
陈磊 → [用户确认] → 刘康 → [用户确认] → 杨锦辉 → [用户确认] → 罗龙飞
```

**为什么这个顺序？** 陈磊后端先出接口 → 刘康前端对接 → 杨锦辉测试验证 → 罗龙飞收尾审核。

**为什么必须等用户确认？**
- 前一人的PR可能审核后有改动（字段名、响应格式、文件路径）
- 后一人如果基于改动前的代码开发，会产生返工和冲突
- 用户的GitHub审核是最終关卡，Claude不能替用户决定"PR是否合格"

**确认点规则：**
- 每个角色完成全部6步（含PR）后，**立即停止**，不做下一角色的任何操作
- 用户手动在GitHub审核PR、确认无误后，说"继续"或"开始{姓名}的任务"
- 只有收到用户明确指令后，才切换到下一角色的分支继续
- **禁止**在用户未确认前一个人的PR的情况下，自动推进到下一人

石义焌（算法）不纳入串行确认流程。算法开发独立于前后端，接口已冻结（`docs/algorithm-interface.md`），变动通过罗龙飞协调。

## 3. 每个角色的执行模板

对每个角色，严格按以下7步执行：

### 步骤1：加载上下文
- 读取 `memory/role-{姓名}.md`（角色卡）
- 读取 `{姓名}个人开发计划.md`（如有）
- 读取 `详细开发计划.md` 中当天该角色的任务行
- 切到该角色的Git分支
- **拉取远程 dev 最新代码合并到当前分支：** `git pull origin dev`

### 步骤2：执行任务
- 按开发计划中"当日任务"列逐项完成
- 产出对应"当日交付"列的文件
- 以"验收标准"列为完成判定
- **每完成一个小任务，用 `/code-review` 自查一遍再继续**

### 步骤3：代码审查
- 对当次变更执行 `/code-review`
- 根据审查意见修改后继续

### 步骤4：编写工作日志
- 文件路径：`docs/logs/YYYY-MM-DD-{姓名}.md`
- 模板：今日任务 → 完成结果 → 遇到的问题 → 解决办法 → 明日计划 → 相关截图或代码提交
- 重点写问题和解决办法，不写流水账

### 步骤5：更新角色记忆
- 更新 `memory/role-{姓名}.md`
- 补充当日完成项和进度
- 更新"明日计划"为开发计划中明天的任务

### 步骤6：提交代码并创建PR
- `git add` 该角色产出的所有文件
- commit 格式：`类型: 描述`（如 `feat:` `test:` `docs:` `fix:`）
- `git push origin {分支名}`
- base: `dev`，head: 该角色分支
- 标题格式：`类型: {姓名} X/X 任务描述`
- body：变更文件列表 + 简要说明
- 使用 `gh pr create`

### 步骤7：停止，等待用户确认 ⛔
- **PR创建后立即停止**，输出简短汇总
- 不做下一角色的任何操作（不切分支、不读文件、不预研）
- 等待用户明确说"继续"、"下一个"、"开始{姓名}"后才继续
- 如果用户说"等下"、"有问题"、"先别继续"，停下来等指示

## 4. 角色执行详情

### 4.1 陈磊（后端）

| 项目 | 内容 |
|---|---|
| 分支 | `feature/chenlei` |
| commit类型 | `feat:` / `fix:` |
| 工作目录 | `backend/` |
| 自动化测试 | `tests/backend/` (pytest) |

典型任务：
- 实现FastAPI接口
- SQLite表操作
- 后台线程
- 文件存储
- services层业务逻辑

### 4.2 刘康（前端）

| 项目 | 内容 |
|---|---|
| 分支 | `feature/liukang` |
| commit类型 | `feat:` / `style:` |
| 工作目录 | `frontend/` |
| 设计参考 | **必读** `design.md`，页面布局严格按第7节 |
| 自动化测试 | `tests/frontend/` (Playwright) |

**⚠️ 前端开发强制前置步骤：**
1. **先读 `design.md`** — 找到对应页面的布局规定（第7节），确认每个区域的位置
2. **再看Figma** — 打开 `design.md` 第0节的Figma链接，对照真实设计稿
3. **对齐色板** — 所有颜色用 `design.md` 第3节的色值，不自行发挥
4. **对齐组件** — 用 `design.md` 第11节规定的组件拆分方式

典型任务：
- Vue页面和组件
- 路由配置
- Element Plus UI
- ECharts图表
- 接口对接
- Playwright E2E测试编写

### 4.3 杨锦辉（测试）

| 项目 | 内容 |
|---|---|
| 分支 | `feature/yangjinhui` |
| commit类型 | `test:` / `docs:` |
| 工作目录 | `tests/` |
| 自动化测试 | `tests/backend/` (pytest), `tests/frontend/` (Playwright) |
| 集成测试 | `tests/integration/` (手动+curl+DB验证) |
| 测试记录 | `tests/integration/test-records/` |
| 问题清单 | `tests/integration/issues/` |
| 测试用例 | `tests/integration/test-cases/` |

典型任务：
- pytest后端测试编写与执行
- Playwright前端E2E测试编写与执行
- 手动curl接口测试
- 数据库验证
- 集成测试用例编写
- 测试记录产出
- 问题清单更新

**杨锦辉的测试三层结构：**
1. `tests/backend/` — pytest自动化，接口+数据库+鉴权
2. `tests/frontend/` — Playwright E2E，页面渲染+交互+Mock API
3. `tests/integration/` — 手动测试记录、用例表、问题清单、截图

### 4.4 罗龙飞（负责人）

| 项目 | 内容 |
|---|---|
| 分支 | `docs/luolongfei` |
| commit类型 | `docs:` |
| 工作目录 | 全局 |
| 产出 | 接口合同、复核记录、PPT素材 |

典型任务：
- 对照检查：代码 vs 需求分析 vs API设计
- 接口对齐：前后端字段是否一致
- 数据库复核：DDL与需求分析对照
- GitHub监督：分支、commit、PR状态
- 算法接口协调：`docs/algorithm-interface.md`
- 收集PPT素材
- 编写个人日志
- 审核前三个角色的PR

**罗龙飞的特殊性：**
- 不写业务代码
- 产出是文档和决策
- 日志要写协调了谁、解决了什么冲突、系统推进到哪一步
- 最后执行，可以利用前三个角色的产出做复核

## 5. 石义焌（算法）状态

石义焌的算法模块（YOLOv11检测、IOU跟踪、6条件行为识别）已于 **6/29 完成并集成**。

### 5.1 已完成模块

```
上传视频 → 创建任务 → [YOLO检测→IOU追踪→行为评估] → 事件入库 → 报警展示 → 历史回放 → 数据看板
                       ↑ 已完成，通过subprocess桥接
```

- `algorithm/detection/detector.py` — YOLOv11检测器
- `algorithm/tracking/tracker.py` — IOU贪心多目标跟踪（DeepSORT降级）
- `algorithm/behavior/behavior.py` — 6条件行为评估（线性回归斜率法）
- `algorithm/pipeline.py` — 全链路编排，每帧写progress.json
- `scripts/pipeline_cli.py` — 子进程CLI桥接（后端.venv→Conda Python）
- `config/default.yaml` — 6参数默认阈值
- `backend/app/api/files.py` — 结果视频/快照文件服务
- 模型：`models/best.pt`（v3+最佳权重）

### 5.2 集成方式

- 后端 `task_service.py` 通过 `subprocess.run` 调用 Conda Python 执行 `pipeline_cli.py`
- `run_video_analysis()` 签名保持 `docs/algorithm-interface.md` 合同不变
- 结果视频编码：MSMF+H264（Windows Media Foundation）
- 实时进度：pipeline每帧写`progress.json`，get_task运行时读取

### 5.3 已知限制

- DeepSORT未安装（当前用IOU tracker降级）
- 阈值需根据实际场景调优
- 结果视频画质可优化
- 石义焌不纳入串行确认流程，算法变动通过罗龙飞协调

## 6. 每日站会（15:00）

罗龙飞在开始工作前确认：
- 今天是几号，按开发计划每人该做什么
- 是否有接口、字段变化需要协调
- 昨天是否有阻塞未解决

## 7. 接口同步（18:00）

罗龙飞在完成陈磊+刘康后检查：
- 刘康前端调用的接口字段是否和陈磊后端返回一致
- 陈磊后端返回字段是否和《详细API设计》一致
- 杨锦辉测试用例是否覆盖当天新增功能

## 8. 收尾检查（21:30）

罗龙飞在全部完成后检查：
- 每人是否提交代码
- 每人是否写个人日志
- 每人是否提PR
- 所有PR是否通过审核
- 是否有不能运行的代码合入dev
- 明天最优先解决什么

## 9. 文件结构约定

```
docs/logs/YYYY-MM-DD-{姓名}.md                              # 个人日志
memory/role-{姓名}.md                                        # 角色记忆
tests/backend/                                               # pytest后端测试
tests/frontend/                                              # Playwright E2E测试
tests/integration/test-records/YYYY-MM-DD-{描述}.md          # 手动测试记录
tests/integration/test-cases/                                # 测试用例表
tests/integration/issues/集成问题清单.md                      # 问题跟踪
tests/integration/reports/                                   # 测试报告
tests/integration/screenshots/                               # 测试截图
```

## 10. 每日执行检查清单

执行完一天的工作后，罗龙飞确认：

- [ ] 陈磊：代码 + 日志 + 记忆 + commit + push + PR
- [ ] 刘康：代码 + 日志 + 记忆 + commit + push + PR
- [ ] 杨锦辉：测试记录 + 日志 + 记忆 + commit + push + PR
- [ ] 罗龙飞：复核记录 + 日志 + 记忆 + commit + push + PR
- [ ] 4个PR全部创建且通过审核，base均为dev
- [ ] pytest全部通过（`python -m pytest -v`）
- [ ] 前端构建成功（`npm run build`）
- [ ] Playwright全部通过（`npx playwright test`）
- [ ] dev分支能正常运行
- [ ] 所有人的日志、记忆已更新到当天日期

## 11. 当前日期判断

每次启动流程时，根据系统日期判断：
- 读取 `详细开发计划.md` 第4节，找到当天对应的任务行
- 如果是6/27（休息日），跳过，直接说"今天休息"
- 如果是7/3之后，说"项目已结束"
- 如果当天任务已全部完成，说"今天的工作已完成"并列出已完成项
