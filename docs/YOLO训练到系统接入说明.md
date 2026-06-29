# YOLOv11 训练到系统接入说明

## 1. 目标

本文说明高空抛物监测系统的算法训练流程，从数据准备、环境准备、模型训练、模型验证，到接入后端 `algorithm.pipeline.run_video_analysis()`。

本项目训练目标不是工业级高精度模型，而是在课程答辩前得到一个可演示、可测试、可说明的高空抛物检测模型。

最终系统闭环：

```text
上传视频
→ 前端绘制 ROI
→ 后端启动分析任务
→ YOLOv11 检测疑似坠落物
→ DeepSORT 或简化 track_id 跟踪
→ 轨迹规则判断疑似高空抛物事件
→ 输出结果视频、事件截图、结构化结果
→ 后端写入数据库
```

## 2. 本机环境准备

### 2.1 Python 环境

项目要求 Python 3.10。当前本机也能跑通 YOLO 环境，但正式演示建议使用虚拟环境隔离：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

YOLO 训练和推理还需要：

```powershell
pip install ultralytics opencv-python torch torchvision
```

如果本机已安装 CUDA 版 PyTorch，可不重复安装。

### 2.2 环境检查

执行：

```powershell
python scripts\check_yolo_env.py --output logs\yolo-env-2026-06-24.json
```

检查项：

- Python 版本
- `ultralytics`
- `opencv-python`
- `torch`
- CUDA 是否可用

本机已验证：

```text
ultralytics 8.4.56
OpenCV 4.13.0.92
torch 2.6.0+cu124
CUDA 可用
GPU: NVIDIA GeForce RTX 3050 Laptop GPU 4GB
```

### 2.3 预训练模型验证

先用 YOLO11n 预训练权重确认推理链路：

```powershell
yolo predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg imgsz=640 save=True
```

本机已跑通，权重保存到：

```text
models/yolo11n.pt
```

推理结果保存到：

```text
runs/detect/outputs/yolo-baseline/2026-06-24-pretrained/
```

## 3. 数据集准备

### 3.1 数据来源

优先使用高空抛物相关数据，不使用跌倒检测、人体 fall detection、普通垃圾检测。

可用来源：

| 来源 | 用途 |
|---|---|
| 阿里云天池高空抛物数据集 | 主数据源，视频抽帧 |
| `firc-dataset` 高空抛物检测数据集 | VOC+YOLO 格式参考 |
| Roboflow Object_Throwing | 抛掷物体检测补充 |
| 自录楼上抛物演示视频 | 课程演示正样本 |
| 无抛物监控片段 | 负样本 |

参考文档：

```text
docs/dataset-sources.md
```

### 3.2 本地目录

大文件不提交 Git，只放本地：

```text
data/videos/          # 原始视频
data/raw/images/      # 抽帧图片
data/raw/labels/      # 原始 YOLO 标签
data/falling_object/  # 训练用 YOLO 数据集
models/               # 模型权重
outputs/              # 分析结果
runs/                 # YOLO 训练/推理输出
```

### 3.3 标注格式

YOLO 标签文件为 `.txt`，每行格式：

```text
class_id center_x center_y width height
```

坐标均为 0 到 1 的归一化值。

本项目统一单类别：

```text
0 falling_object
```

示例：

```text
0 0.512300 0.438000 0.061000 0.074000
```

### 3.4 视频抽帧

如果数据来源是视频，先抽帧：

```powershell
python scripts\prepare_dataset.py `
  --source data\raw `
  --output data\falling_object `
  --video-dir data\videos `
  --frame-step 10
```

含义：

- 每 10 帧抽 1 帧
- 抽帧图片写入 `data/raw/images/`
- 后续人工标注或导入已有标签

### 3.5 数据格式整理

已有图片和标签后，执行：

```powershell
python scripts\prepare_dataset.py `
  --source data\raw `
  --output data\falling_object `
  --val-ratio 0.2
```

脚本会完成：

- 读取 `data/raw/images/`
- 读取同名 `data/raw/labels/*.txt`
- 将所有类别 ID 统一为 `0`
- 划分 `train/val`
- 生成 `data.yaml`
- 无标签图片生成空标签，作为负样本

输出结构：

```text
data/falling_object/
  images/train/
  images/val/
  labels/train/
  labels/val/
  classes.txt
  data.yaml
```

## 4. 训练前检查

训练前必须检查：

```powershell
Get-ChildItem data\falling_object\images\train
Get-ChildItem data\falling_object\labels\train
Get-Content data\falling_object\data.yaml
```

重点确认：

- 图片和标签文件名一一对应
- 标签类别只有 `0`
- `data.yaml` 中 `names: 0: falling_object`
- 负样本允许空 `.txt`
- 不要把跌倒检测数据混入训练集

## 5. YOLOv11 训练

### 5.1 首版训练命令

RTX3050 4GB 显存建议先用小模型和小 batch：

```powershell
yolo detect train `
  model=models\yolo11n.pt `
  data=data\falling_object\data.yaml `
  imgsz=640 `
  epochs=50 `
  batch=1 `
  workers=0 `
  project=runs\train `
  name=falling_object_yolo11n
```

参数说明：

| 参数 | 说明 |
|---|---|
| `model` | 预训练权重 |
| `data` | 数据集配置 |
| `imgsz` | 输入尺寸 |
| `epochs` | 训练轮数 |
| `batch` | 批大小，显存小用 1 |
| `workers` | Windows 下用 0 更稳 |
| `project/name` | 输出目录 |

### 5.2 输出文件

训练完成后重点看：

```text
runs/train/falling_object_yolo11n/weights/best.pt
runs/train/falling_object_yolo11n/weights/last.pt
runs/train/falling_object_yolo11n/results.png
runs/train/falling_object_yolo11n/confusion_matrix.png
```

系统接入优先使用：

```text
best.pt
```

### 5.3 训练指标

需要记录到测试报告和 PPT：

- Precision
- Recall
- mAP50
- mAP50-95
- loss 曲线
- 训练轮数
- 数据集样本数量

指标含义：

| 指标 | 含义 | 判断方式 |
|---|---|---|
| Precision | 预测为抛物的检测框中，有多少是真的 | 越高误报越少 |
| Recall | 真实抛物目标中，有多少被检测出来 | 越高漏检越少 |
| mAP50 | IoU 阈值为 0.5 时的平均检测精度 | 看模型能否大致框中目标 |
| mAP50-95 | IoU 从 0.5 到 0.95 多档阈值的平均检测精度 | 更严格，看检测框是否精确 |
| box_loss | 检测框位置和大小误差 | 越低框越准 |
| cls_loss | 类别分类误差 | 本项目单类别，越低越好 |
| dfl_loss | 边框精细定位误差 | 越低边界越准 |
| Instances | 当前 batch 或验证集中的目标框数量 | 不是性能指标，用于观察样本量 |
| GPU_mem | 训练时占用的显存 | 用于判断 batch/imgsz 是否合适 |
| Images | 验证集图片数量 | 用于说明验证规模 |
| Epoch | 当前训练轮数 | 用于说明训练进度 |

演示判断优先级：

```text
优先看 Recall 和 mAP50，保证演示视频中的下落物能被检出。
误报多时看 Precision。
框不准时看 mAP50-95、box_loss、dfl_loss。
```

课程演示中不要承诺工业级准确率，只说明：

```text
模型用于课程原型演示，可识别演示视频中的疑似坠落物。
```

## 6. 模型验证

### 6.1 图片验证

```powershell
yolo detect predict `
  model=runs\train\falling_object_yolo11n\weights\best.pt `
  source=data\falling_object\images\val `
  imgsz=640 `
  conf=0.35 `
  save=True
```

检查：

- 是否能框出坠落物
- 是否误检墙面、窗户、人
- 小目标是否漏检

### 6.2 视频验证

```powershell
yolo detect predict `
  model=runs\train\falling_object_yolo11n\weights\best.pt `
  source=data\videos\demo.mp4 `
  imgsz=640 `
  conf=0.35 `
  save=True
```

检查：

- 推理速度是否可接受
- 检测框是否连续
- 结果视频是否可播放
- 演示视频中至少能检测到关键坠落物

### 6.3 权重固化

验证通过后复制：

```powershell
Copy-Item runs\train\falling_object_yolo11n\weights\best.pt models\falling_object_yolo11n.pt
```

系统默认读取：

```text
models/falling_object_yolo11n.pt
```

## 7. 接入系统

### 7.1 接口入口

后端只调用一个算法入口：

```python
from algorithm.pipeline import run_video_analysis
```

函数签名固定：

```python
run_video_analysis(
    video_path: str,
    output_dir: str,
    roi: dict[str, int],
    settings: dict[str, Any],
) -> PipelineResult
```

不要改字段名，避免前后端联调断开。

### 7.2 Pipeline 内部流程

完整实现应包含：

```text
1. 检查模型文件是否存在
2. 加载 YOLOv11 权重
3. OpenCV 打开上传视频
4. 逐帧读取
5. 在 ROI 内或全图执行 YOLO 检测
6. 过滤低置信度检测框
7. 将检测框送入 DeepSORT
8. 得到 track_id 和轨迹中心点
9. 判断轨迹是否持续向下
10. 判断轨迹是否主要位于 ROI 内
11. 触发疑似高空抛物事件
12. 保存事件截图
13. 绘制检测框、track_id、轨迹、ROI
14. 输出结果视频
15. 返回 PipelineResult
```

### 7.3 检测结果字段

每个检测框写入：

```python
{
    "frame_id": 150,
    "bbox_x": 100,
    "bbox_y": 80,
    "bbox_width": 30,
    "bbox_height": 30,
    "confidence": 0.76,
    "class_name": "falling_object",
}
```

### 7.4 跟踪结果字段

每个轨迹点写入：

```python
{
    "track_id": 3,
    "frame_id": 150,
    "timestamp": 5.0,
    "center_x": 115,
    "center_y": 95,
    "bbox_x": 100,
    "bbox_y": 80,
    "bbox_width": 30,
    "bbox_height": 30,
}
```

### 7.5 事件字段

触发事件后写入：

```python
{
    "track_id": 3,
    "confidence": 0.82,
    "snapshot_path": "outputs/task_1/snapshots/event_1.jpg",
    "created_at": "2026-06-28 20:10:00",
}
```

### 7.6 返回结果

成功：

```python
PipelineResult(
    status="success",
    total_frames=300,
    processed_frames=300,
    result_video_path="outputs/task_1/result.mp4",
    events=[...],
    detection_results=[...],
    tracking_results=[...],
    error_message=None,
)
```

失败：

```python
PipelineResult(
    status="failed",
    error_message="模型文件不存在",
)
```

## 8. 轨迹规则

本项目不精确区分“人为抛出”和“自然掉落”，统一叫：

```text
疑似高空抛物事件
```

建议规则：

| 条件 | 参数 |
|---|---|
| YOLO 置信度达标 | `detect_confidence >= 0.35` |
| 轨迹连续帧数达标 | `min_track_frames >= 5` |
| y 坐标整体向下 | `downward_ratio >= 0.7` |
| 垂直位移足够 | `min_vertical_distance >= 80` |
| 轨迹多数点在 ROI 内 | `roi_required_ratio >= 0.7` |
| 同一 track 冷却 | `alarm_cooldown_seconds >= 10` |

判断逻辑：

```text
如果一个 track_id 的中心点连续向下，
且总垂直位移超过阈值，
且多数轨迹点位于 ROI 内，
则判定为疑似高空抛物事件。
```

## 9. 后端写入

后端后台线程调用算法后：

| PipelineResult 字段 | 后端处理 |
|---|---|
| `status` | 更新 `video_tasks.status` |
| `total_frames` | 更新任务总帧数 |
| `processed_frames` | 更新真实处理帧数 |
| `result_video_path` | 保存结果视频路径 |
| `events` | 写入 `events` 表 |
| `detection_results` | 写入 `detection_results` 表 |
| `tracking_results` | 写入 `tracking_results` 表 |
| `error_message` | 写入失败原因 |

前端通过任务查询接口轮询进度，成功后展示结果视频和事件列表。

## 10. 演示前检查清单

### 10.1 文件检查

```text
models/falling_object_yolo11n.pt
data/videos/demo.mp4
outputs/
events/
```

### 10.2 命令检查

```powershell
python scripts\check_yolo_env.py
python -m pytest tests\algorithm -q
python -m compileall algorithm scripts tests\algorithm
```

### 10.3 系统检查

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

访问：

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/docs
```

### 10.4 演示检查

```text
管理员登录
上传演示视频
绘制 ROI
启动分析
等待任务完成
查看结果视频
查看报警事件
查看历史回放
查看数据看板
```

## 11. 常见问题

### 11.1 显存不足

处理：

```powershell
yolo detect train model=models\yolo11n.pt data=data\falling_object\data.yaml imgsz=480 batch=1 workers=0
```

优先降低：

- `batch`
- `imgsz`
- `epochs`

### 11.2 检测不到小目标

处理：

- 增加高空抛物近似场景样本
- 增加小物体标注
- 降低 `conf` 到 0.25 测试
- 使用清晰、短时长演示视频

### 11.3 误检太多

处理：

- 增加负样本
- 删除跌倒、垃圾、无关目标数据
- 提高 `detect_confidence`
- 用 ROI 限制判断区域

### 11.4 DeepSORT 接入慢

备用：

```text
先用简化 track_id 按检测框中心点距离匹配，
保证上传视频 → 检测 → 轨迹 → 事件入库闭环。
后续再替换 DeepSORT。
```

### 11.5 ONNX 导出失败

不阻塞主演示。记录为优化尝试：

```powershell
yolo export model=models\falling_object_yolo11n.pt format=onnx imgsz=640
```

失败时继续使用 `.pt` 权重。

## 12. 答辩表述

可说明：

```text
本系统使用 YOLOv11 完成疑似坠落物检测，
再通过目标跟踪获得轨迹，
最后结合 ROI、持续向下运动、垂直位移和冷却时间规则判断疑似高空抛物事件。
```

不要说明：

```text
系统能工业级准确识别所有高空抛物。
系统能精确区分人为抛出和自然掉落。
系统已完成真实边缘设备部署。
```

## 13. 最小交付标准

训练与接入至少满足：

```text
1. 有可说明的数据来源
2. 有 YOLO 格式训练目录
3. 有 best.pt 或可用预训练权重
4. 有一段演示视频能输出检测框
5. PipelineResult 字段符合后端合同
6. 结果视频可播放
7. 事件能入库或能说明当前阻塞点
```
