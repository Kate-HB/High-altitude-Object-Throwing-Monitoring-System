# 石义焌 - 算法开发

## 基本信息
- 角色：算法负责人
- 分支：`feature/shiyijun`
- 工作目录：`algorithm/` `scripts/` `config/`
- 测试目录：`tests/algorithm/`
- Python环境：Conda base（torch 2.6.0+cu124, ultralytics 8.4.56）

## 已完成

### 6月24日
- 数据集来源整理 (`docs/dataset-sources.md`)
- 数据集标注格式说明 (`docs/dataset.md`)
- YOLO环境确认脚本 (`scripts/check_yolo_env.py`)
- 数据预处理脚本 (`scripts/prepare_dataset.py`)

### 6月25日
- 标注脚本 (`scripts/annotate.py`)
- YOLO训练脚本 (`scripts/train.py`)
- 模型测试脚本 (`scripts/test_model.py`)
- 训练记录与参数总结 (`docs/训练记录与参数总结.md`)

### 6月26日
- 检测模块 `algorithm/detection/detector.py` — YOLOv11包装器
- 跟踪模块 `algorithm/tracking/tracker.py` — IOU贪心多目标跟踪（DeepSORT降级方案）
- 行为分析模块 `algorithm/behavior/behavior.py` — 6条件轨迹评估器
- 主流程编排 `algorithm/pipeline.py` — 检测→跟踪→行为 全链路
- 算法接口合同冻结 `docs/algorithm-interface.md`
- 工作日志 `docs/logs/2026-06-26-石义焌.md`

### 6月28日
- `scripts/pipeline_cli.py` — 子进程桥接（后端.venv→算法Conda）
- 配置文件 `config/default.yaml` — 6参数默认阈值
- DeepSORT安装（`deep-sort-realtime 1.3.2`，安装在.venv-labelimg）
- 后端集成：task_service.py 改用subprocess调用pipeline_cli
- ROI归一化处理（None值兼容）
- 跟踪器输出修复（active_track_ids全量输出）
- 检测器API修正（model(frame)→model.predict(frame, stream=False)）
- 视频编码修复：FFMPEG libopenh264损坏→改用MSMF+H264
- 最佳模型部署：`runs/detect/runs/train/falling_object_yolo11n_v3+/weights/best.pt` → `models/best.pt`
- 工作日志 `docs/logs/2026-06-28-石义焌.md`

### 6月29日
- `backend/app/api/files.py` — 文件服务端点（/api/files，含路径越界保护）
- 实时进度：pipeline每帧写`progress.json`，task_service读取实现轮询进度
- ROI检测级过滤：检测框中心不在ROI范围内丢弃
- 行为分析修复：帧间下降率改为线性回归斜率（解决检测框抖动导致downward_ratio≈0）
- 快照画框：快照保存移到绘制后，含检测框+轨迹+ROI+触发目标红框标注
- 前端事件列表添加快照缩略图，点击overlay弹窗放大
- 前端页面保活：MainLayout router-view加keep-alive，切换页面不丢状态
- 默认阈值调整：min_vertical_distance 80→50, downward_ratio改为斜率法, roi_required_ratio 0.7→0.5
- 工作日志 `docs/logs/2026-06-29-石义焌.md`

## 明日计划（6月30日）

- 结果视频优化（画质、帧率、文件大小）
- 阈值调优（基于更多测试视频）
- 首次完整联调（与罗龙飞配合）
- 演示视频准备

## 技术笔记

- Conda base: `D:\Soft\Conda\python.exe`（有torch+ultralytics）
- 后端.venv: `.venv/Scripts/python.exe`（有FastAPI+OpenCV，无torch）
- .venv-labelimg: 仅用于labelImg标注工具，不用于ML
- 视频编码：MSMF后端+H264 FourCC，避免FFMPEG的openh264 DLL问题
- 行为6条件：detect_confidence→向下趋势（线性回归斜率）→min_vertical_distance→min_track_frames→roi_required_ratio→alarm_cooldown
- 模型路径：`models/best.pt`（v3+最佳权重）
