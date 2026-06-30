# GitHub团队协作指南

## 1. 文档目标

本项目使用GitHub统一托管代码，采用：

```text
Issue任务管理 + 独立功能分支 + Pull Request审核 + main稳定版本
```

这套流程解决四个问题：

1. 五人可以同时开发，不互相覆盖代码。
2. 每项代码都能找到作者、修改原因和历史版本。
3. 未完成或有问题的代码不会破坏答辩版本。
4. 出现错误时可以定位、比较和恢复。

## 2. Git与GitHub的区别

### 2.1 Git

Git是安装在电脑上的版本管理工具，主要作用：

- 记录每次代码修改。
- 创建独立开发分支。
- 比较不同版本。
- 合并多人代码。
- 恢复历史版本。

### 2.2 GitHub

GitHub是远程代码托管和团队协作平台，主要作用：

- 保存远程仓库。
- 在不同电脑之间同步代码。
- 分配Issue任务。
- 发起Pull Request代码审核。
- 保存项目提交和协作记录。

### 2.3 常用概念

| 概念 | 含义 | 作用 |
|---|---|---|
| Repository | 仓库 | 保存项目代码和历史 |
| Clone | 克隆 | 第一次将远程仓库复制到本地 |
| Commit | 提交 | 在本地记录一次有意义的修改 |
| Push | 推送 | 将本地提交上传到GitHub |
| Pull | 拉取 | 获取并合并远程最新代码 |
| Branch | 分支 | 独立开发空间 |
| Issue | 任务单 | 记录任务、问题和负责人 |
| Pull Request | 合并请求，简称PR | 请求审核并合并代码 |
| Merge | 合并 | 将一个分支的修改加入另一个分支 |
| Conflict | 冲突 | 多人修改同一位置，Git无法自动决定结果 |

## 3. 项目分支设计

本项目只保留两类长期分支：

```text
main：稳定、可演示、可交付版本
dev：日常开发集成版本
```

每项任务创建一个短期功能分支：

```text
feature/luolongfei-system-integration
feature/shiyijun-yolo-training
feature/liukang-monitor-page
feature/chenlei-upload-api
feature/yangjinhui-alarm-test
```

修复缺陷使用：

```text
fix/姓名-问题
```

示例：

```text
fix/chenlei-video-upload-error
```

### 3.1 main分支

目的：

- 始终保存能够正常运行的版本。
- 用于答辩演示和最终交付。
- 普通成员不得直接向main推送代码。

### 3.2 dev分支

目的：

- 汇总各成员已经完成并审核的功能。
- 用于联调和测试。
- 稳定后再合并到main。

### 3.3 功能分支

目的：

- 每个人在自己的任务空间中开发。
- 未完成的代码不会影响其他人。
- 功能完成后通过PR合并到dev。

原则：一个分支只完成一个明确任务，合并后删除。

## 4. 成员协作权限

| 成员 | GitHub职责 |
|---|---|
| 罗龙飞 | 仓库管理员；分配Issue；审核工程代码；处理冲突；将dev合并到main；发布版本 |
| 石义焌 | 审核算法代码；维护数据、模型和训练说明；协助处理算法分支冲突 |
| 刘康 | 维护前端分支；通过PR提交前端功能 |
| 陈磊 | 维护后端分支；通过PR提交API和数据库功能 |
| 杨锦辉 | 维护测试、ROI、报警和文档分支；提交测试结果 |

所有成员均可：

- 克隆和拉取仓库。
- 创建和推送个人功能分支。
- 创建Issue和PR。
- 评论代码和报告问题。

## 5. 仓库首次创建

由罗龙飞完成。

### 5.1 创建GitHub仓库

1. 登录GitHub。
2. 点击`New repository`。
3. 输入仓库名称。
4. 选择`Private`。
5. 创建仓库。
6. 在`Settings → Collaborators`邀请其他四人。

### 5.2 上传现有项目

在项目根目录打开PowerShell：

```bash
git init
git branch -M main
git add .
git commit -m "chore: initialize project"
git remote add origin 仓库地址
git push -u origin main
```

命令作用：

| 命令 | 作用 |
|---|---|
| `git init` | 将当前目录初始化为Git仓库 |
| `git branch -M main` | 将当前分支命名为main |
| `git add .` | 将当前修改放入暂存区 |
| `git commit` | 创建本地版本记录 |
| `git remote add origin` | 绑定GitHub远程仓库 |
| `git push` | 将本地提交推送到GitHub |

### 5.3 创建dev分支

```bash
git switch -c dev
git push -u origin dev
```

完成后切回：

```bash
git switch main
```

### 5.4 保护分支

在GitHub进入：

```text
Settings → Branches/Rules → Add branch protection rule
```

分别保护`main`和`dev`：

- 要求通过Pull Request合并。
- 禁止直接推送。
- `main`至少由罗龙飞确认。
- 算法PR由石义焌审核，工程PR由罗龙飞审核。

目的：防止误操作直接破坏稳定代码。

## 6. 其他成员首次加入

每人只需要克隆一次：

```bash
git clone 仓库地址
cd 项目目录
git switch dev
git pull origin dev
```

设置个人身份：

```bash
git config --global user.name "GitHub用户名"
git config --global user.email "GitHub邮箱"
```

身份信息会记录在提交历史中。

查看远程仓库：

```bash
git remote -v
```

查看当前状态：

```bash
git status
```

## 7. 标准任务流程

每项任务必须按以下顺序执行。

### 7.1 第一步：创建Issue

负责人在GitHub创建Issue，例如：

```text
标题：实现视频上传与格式校验
负责人：陈磊
目标：支持MP4/AVI上传，拒绝损坏文件
验收条件：
1. 正常视频可以上传
2. 非视频文件被拒绝
3. 接口返回任务ID
4. 提供测试截图
```

Issue的目的：

- 明确谁负责什么。
- 明确完成标准。
- 保存问题讨论和过程证据。
- 方便编写日志、周志和答辩材料。

### 7.2 第二步：同步dev

每次开始任务前执行：

```bash
git switch dev
git pull origin dev
```

目的：基于团队最新代码开发，降低后续冲突。

### 7.3 第三步：创建功能分支

```bash
git switch -c feature/chenlei-video-upload
```

目的：将当前任务与dev隔离。

检查当前分支：

```bash
git branch --show-current
```

### 7.4 第四步：开发并检查修改

开发过程中随时查看：

```bash
git status
git diff
```

- `git status`：查看修改、新增和删除了哪些文件。
- `git diff`：查看代码具体改动。

### 7.5 第五步：提交代码

先只添加本任务文件：

```bash
git add backend/api/upload.py
git add backend/tests/test_upload.py
```

再提交：

```bash
git commit -m "feat: add video upload validation"
```

目的：在本地创建一个可追踪、可恢复的版本节点。

不要习惯性使用`git add .`，避免上传无关文件、模型、视频或密码。

### 7.6 第六步：推送功能分支

第一次推送：

```bash
git push -u origin feature/chenlei-video-upload
```

之后继续修改时：

```bash
git add 具体文件
git commit -m "fix: handle damaged video file"
git push
```

### 7.7 第七步：创建Pull Request

在GitHub点击`Compare & pull request`：

```text
base：dev
compare：feature/chenlei-video-upload
```

PR内容至少包括：

```text
完成内容：
- 新增视频上传接口
- 增加MP4/AVI格式校验

测试方式：
- 上传正常MP4成功
- 上传TXT文件返回错误
- 上传损坏视频返回错误

关联Issue：
Closes #12

注意事项：
- 上传目录需要提前创建
```

目的：

- 合并前让其他成员检查代码。
- 记录功能说明和测试证据。
- 自动关闭对应Issue。

### 7.8 第八步：审核PR

审核人检查：

- 是否只修改本任务相关内容。
- 功能是否满足Issue验收条件。
- 是否包含密码、数据集、视频或模型。
- 是否能正常启动。
- 是否破坏原有功能。
- 是否提供必要测试。

**审核操作方式：**

在GitHub打开PR，进入**Files changed**标签，逐文件查看改动。对有问题代码行悬停点击蓝色`+`写评论。

全部看完后点右上角**Review changes**：

- **Comment**：有意见但不做决定。
- **Approve**：代码合格，准许合并。
- **Request changes**：存在必须修改的问题。

若需要本地跑代码验证：

```bash
git fetch origin
git switch -c review/某人-某功能 origin/feature/某人-某功能
# 启动前后端手动验证
git switch dev
git branch -d review/某人-某功能
```

发现小问题直接在PR行评论；大问题点**Request changes**。验证通过后点**Squash and merge**合并。

审核人有问题时在PR中写明修改位置和原因。开发者修改后继续：

```bash
git add 具体文件
git commit -m "fix: update upload error handling"
git push
```

PR会自动更新，不需要重新创建。

### 7.9 第九步：合并并删除分支

审核通过后使用：

```text
Squash and merge
```

目的：将一个任务的多个零散提交压缩成一条清晰记录。

合并后在GitHub删除功能分支。

本地同步：

```bash
git switch dev
git pull origin dev
git branch -d feature/chenlei-video-upload
```

## 8. 每日操作模板

开始工作：

```bash
git switch dev
git pull origin dev
git switch 功能分支
git merge dev
```

若当天首次创建任务分支：

```bash
git switch dev
git pull origin dev
git switch -c feature/姓名-任务
```

结束工作：

```bash
git status
git add 具体文件
git commit -m "feat: describe completed work"
git push
```

未完成功能也可以提交到个人分支，但提交信息应明确：

```bash
git commit -m "wip: complete upload page layout"
```

`wip`表示工作尚未完成，不应立即合并。

## 9. 提交信息规范

格式：

```text
类型: 简短描述
```

| 类型 | 用途 | 示例 |
|---|---|---|
| `feat` | 新增功能 | `feat: add event history page` |
| `fix` | 修复缺陷 | `fix: prevent duplicate alarms` |
| `docs` | 修改文档 | `docs: update deployment guide` |
| `test` | 增加或修改测试 | `test: add damaged video cases` |
| `refactor` | 不改变功能的代码调整 | `refactor: split event service` |
| `chore` | 配置、依赖等杂项 | `chore: update gitignore` |
| `wip` | 尚未完成的阶段工作 | `wip: build dashboard charts` |

要求：

- 一次提交只做一类事情。
- 描述具体修改，禁止使用“更新代码”“修改一下”。
- 提交前运行相关模块或测试。

## 10. 拉取、获取与推送的区别

### 10.1 git fetch

```bash
git fetch origin
```

只获取远程状态，不修改当前代码。适合检查远程更新。

### 10.2 git pull

```bash
git pull origin dev
```

等于获取远程代码并合并到当前分支。开始开发前使用。

### 10.3 git push

```bash
git push
```

将本地已经commit的记录上传到GitHub。未commit的文件不会上传。

## 11. 冲突产生原因与处理

### 11.1 常见原因

- 两人修改同一个文件的同一位置。
- 某人长时间不拉取dev。
- 直接在dev或main开发。
- 一个分支包含多个无关任务。

### 11.2 预防措施

- 开始任务前拉取最新dev。
- 明确模块负责人。
- 尽量避免多人同时修改同一文件。
- 每天至少同步一次。
- 小步提交，尽快创建PR。

### 11.3 冲突处理

普通成员发生冲突时不要强制推送，通知罗龙飞。

基本处理流程：

```bash
git switch feature/个人任务
git fetch origin
git merge origin/dev
```

冲突文件中会出现：

```text
<<<<<<< HEAD
当前分支内容
=======
dev分支内容
>>>>>>> origin/dev
```

人工保留正确内容并删除标记，然后：

```bash
git add 冲突文件
git commit -m "merge: resolve dev conflict"
git push
```

处理前必须与相关文件负责人确认应保留的逻辑。

## 12. 错误恢复

### 12.1 查看提交历史

```bash
git log --oneline --graph --all
```

作用：查看提交、分支和合并关系。

### 12.2 放弃尚未暂存的单个文件修改

```bash
git restore 文件路径
```

该操作会丢弃本地修改，执行前必须确认。

### 12.3 取消暂存

```bash
git restore --staged 文件路径
```

文件内容不会丢失，只从暂存区移除。

### 12.4 撤销已经共享的提交

```bash
git revert 提交编号
```

作用：创建一个反向提交，安全撤销历史修改。

团队仓库禁止随意使用：

```text
git reset --hard
git push --force
```

这两条命令可能删除本地工作或覆盖他人提交。

## 13. 大文件与敏感信息管理

### 13.1 GitHub不保存的内容

- FADE和天池数据集。
- 原始视频、结果视频和事件截图。
- YOLO模型权重、ONNX模型。
- `.venv`、`node_modules`。
- SQLite运行数据库。
- 缓存、日志和临时文件。
- API密钥、密码和个人配置。

### 13.2 推荐.gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Frontend
node_modules/
dist/

# IDE
.idea/
.vscode/

# Environment and secrets
.env
.env.*
!.env.example

# Runtime data
data/
datasets/
uploads/
outputs/
events/
logs/
*.db
*.sqlite
*.sqlite3

# Models and media
*.pt
*.pth
*.onnx
*.engine
*.mp4
*.avi
*.mov
*.mkv

# OS
.DS_Store
Thumbs.db
```

### 13.3 大文件共享

使用统一网盘目录保存：

```text
datasets/
models/
demo-videos/
test-videos/
```

在README记录：

- 下载链接。
- 文件名称。
- 文件版本。
- 文件大小。
- 校验值。
- 放置目录。

模型示例：

```text
文件：best-v2.pt
训练日期：2026-06-28
数据版本：fade-clean-v2
放置位置：backend/models/best.pt
SHA256：……
```

只有确需版本管理的大文件才使用Git LFS。

## 14. 项目目录责任

建议目录：

```text
project/
├─ frontend/          # 刘康
├─ backend/           # 陈磊
├─ algorithm/         # 石义焌
├─ tests/             # 杨锦辉
├─ docs/              # 全员，罗龙飞审核
├─ scripts/           # 数据转换、启动和部署脚本
├─ config/            # 配置示例
├─ README.md
├─ requirements.txt
└─ .gitignore
```

目录负责人并非唯一修改者，但跨模块修改前应先通知负责人。

## 15. Issue使用规则

每个Issue必须包含：

- 背景或问题。
- 负责人。
- 任务范围。
- 验收条件。
- 截止时间。
- 相关截图、日志或链接。

标签建议：

```text
frontend
backend
algorithm
test
document
bug
priority-high
blocked
```

状态可用GitHub Project管理：

```text
待处理 → 开发中 → 待审核 → 测试中 → 已完成
```

## 16. Pull Request审核规则

### 16.1 PR必须满足

- 关联Issue。
- 描述修改内容。
- 说明测试方法和结果。
- 无数据集、模型、视频和密钥。
- 无无关文件。
- 当前功能能够运行。

### 16.2 审核分工

- 算法、训练、检测、跟踪：石义焌主审，罗龙飞确认集成。
- 前端、后端、数据库、部署：罗龙飞主审。
- 测试报告和测试代码：杨锦辉整理，罗龙飞审核。

### 16.3 禁止合并情况

- 功能未完成。
- 没有测试。
- 出现明显报错。
- 与dev冲突未解决。
- 包含密码或大文件。
- 擅自修改无关模块。

## 17. dev发布到main

只有罗龙飞执行。

发布前检查：

1. 前后端能够启动。
2. 主演示视频完整运行。
3. 报警、存储、回放正常。
4. 测试通过。
5. 模型和配置说明完整。
6. 当前版本已在备机验证。

在GitHub创建PR：

```text
dev → main
```

PR标题示例：

```text
release: v0.1 complete detection workflow
```

合并后创建版本标签：

```bash
git switch main
git pull origin main
git tag -a v0.1.0 -m "First complete demo version"
git push origin v0.1.0
```

标签作用：固定一个可随时找回的演示版本。

建议版本：

```text
v0.1.0：首次完整闭环
v0.2.0：功能全部完成
v1.0.0：最终答辩版本
```

## 18. 五人协作示例

陈磊开发上传接口：

```bash
git switch dev
git pull origin dev
git switch -c feature/chenlei-video-upload
# 编写代码和测试
git add backend/api/upload.py backend/tests/test_upload.py
git commit -m "feat: add video upload API"
git push -u origin feature/chenlei-video-upload
```

陈磊创建PR到dev，罗龙飞审核并合并。

刘康随后开发上传页面：

```bash
git switch dev
git pull origin dev
git switch -c feature/liukang-upload-page
# 调用陈磊已合并的接口
git add frontend/src/views/Upload.vue
git commit -m "feat: add video upload page"
git push -u origin feature/liukang-upload-page
```

这样前端始终基于已经进入dev的后端接口开发，减少接口不一致。

## 19. 每日团队检查

每日结束前由罗龙飞检查：

- 每人是否有对应Issue。
- 正在开发的任务是否有独立分支。
- 已完成任务是否创建PR。
- PR是否包含测试说明。
- 是否有人直接修改main或dev。
- 是否误传数据集、视频、模型或密钥。
- dev是否仍能启动。

每两天：

- 将已审核功能合并到dev。
- 在主演示机运行完整流程。
- 记录集成问题并创建Issue。
- 保存测试截图，供日志、周志、测试报告和PPT使用。

## 20. 最低命令清单

普通成员必须掌握：

```bash
git status
git switch 分支名
git switch -c 新分支名
git pull origin dev
git add 文件路径
git commit -m "类型: 描述"
git push
git log --oneline
```

负责人额外掌握：

```bash
git fetch origin
git merge origin/dev
git branch -d 分支名
git revert 提交编号
git tag
```

## 21. 核心纪律

1. 禁止直接在main开发。
2. 禁止未经PR向dev合并。
3. 一个分支只处理一个任务。
4. 开工前先同步dev。
5. 提交前检查`git status`和`git diff`。
6. 禁止提交数据集、视频、模型、密码和运行数据库。
7. 禁止使用`git push --force`。
8. 冲突不确定时停止操作，由罗龙飞协调。
9. 合并前必须测试。
10. 每个稳定版本必须打标签。
