# 算法 Pipeline 输入输出字段说明

## 1. 文档说明

本文档定义后端调用算法 Pipeline 的统一接口，是后端（陈磊）和算法（石义焌）之间的**接口合同**。

本文档一旦定稿，输入输出字段不再随意变更。如需修改，由罗龙飞确认后同步更新本文档、`algorithm/pipeline.py` 和《详细API设计》第 12 节。

## 2. 调用方式

后端通过以下模块级函数调用算法：

```python
from algorithm.pipeline import run_video_analysis

result = run_video_analysis(
    video_path="uploads/demo.mp4",
    output_dir="outputs/",
    roi={"x": 100, "y": 50, "width": 400, "height": 300},
    settings={
        "detect_confidence": 0.35,
        "downward_ratio": 0.7,
        "min_vertical_distance": 80,
        "min_track_frames": 5,
        "roi_required_ratio": 0.7,
        "alarm_cooldown_seconds": 10,
    },
)
```

- 函数名：`run_video_analysis`
- 位置：`algorithm/pipeline.py`
- 调用方式：同步函数，在后端后台线程中调用，避免阻塞 FastAPI 主线程
- 返回值：`PipelineResult` 数据类实例（见第 4 节）

## 3. 输入参数

### 3.1 video_path（必填）

| 项目 | 说明 |
|---|---|
| 类型 | `str` |
| 含义 | 待分析的原视频文件路径 |
| 来源 | 后端 `POST /api/videos/upload` 保存后的文件路径 |
| 示例 | `"uploads/demo.mp4"` |
| 约束 | 文件必须存在，否则算法返回 `status=failed` |

### 3.2 output_dir（必填）

| 项目 | 说明 |
|---|---|
| 类型 | `str` |
| 含义 | 结果视频和事件截图的输出目录 |
| 来源 | 后端根据任务 ID 创建，格式 `outputs/task_{id}/` |
| 示例 | `"outputs/task_1/"` |
| 约束 | 目录不存在时算法自行创建 |

### 3.3 roi（必填）

| 项目 | 说明 |
|---|---|
| 类型 | `dict` |
| 含义 | 管理员在前端绘制的 ROI 矩形区域 |

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| x | int | ROI 左上角 x 坐标（像素） |
| y | int | ROI 左上角 y 坐标（像素） |
| width | int | ROI 宽度（像素） |
| height | int | ROI 高度（像素） |

示例：

```json
{
  "x": 100,
  "y": 50,
  "width": 400,
  "height": 300
}
```

对应数据库 `video_tasks` 表的 `roi_x`、`roi_y`、`roi_width`、`roi_height` 字段。后端负责将 dict 拆分为四个字段入库，或将四个字段组装为 dict 传给算法。

### 3.4 settings（必填）

| 项目 | 说明 |
|---|---|
| 类型 | `dict` |
| 含义 | 检测和报警参数，从 `system_settings` 表读取 |
| 来源 | 后端调用 `GET /api/settings` 或直接查表 |

字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| detect_confidence | float | 0.35 | YOLOv11 检测置信度阈值，低于此值的检测框被丢弃 |
| downward_ratio | float | 0.7 | 连续下降帧占比阈值，轨迹中下降帧比例低于此值不触发报警 |
| min_vertical_distance | int | 80 | 最小垂直位移（像素），轨迹总下降距离低于此值不触发报警 |
| min_track_frames | int | 5 | 最小连续跟踪帧数，短于此帧数的目标不触发报警 |
| roi_required_ratio | float | 0.7 | ROI 内轨迹点占比阈值，轨迹点在 ROI 内的比例低于此值不触发报警 |
| alarm_cooldown_seconds | int | 10 | 报警冷却时间（秒），同一 track_id 在冷却时间内不重复报警 |

对应数据库 `system_settings` 表，字段名一一对应。

## 4. 输出结果

### 4.1 PipelineResult 结构

```python
@dataclass
class PipelineResult:
    status: str                        # "success" | "failed"
    total_frames: int                  # 视频总帧数
    processed_frames: int              # 实际处理帧数
    result_video_path: str | None      # 结果视频路径
    events: list[EventInfo]            # 疑似事件列表
    detection_results: list[DetectionInfo]  # 检测结果列表（可选，用于调试）
    tracking_results: list[TrackingInfo]    # 跟踪结果列表（可选，用于调试）
    error_message: str | None          # 失败原因
```

### 4.2 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| status | string | `"success"` 表示分析完成；`"failed"` 表示失败 |
| total_frames | int | 视频总帧数 |
| processed_frames | int | 算法实际处理的帧数（可能因抽帧小于 total_frames） |
| result_video_path | string 或 null | 结果视频相对路径，如 `"outputs/task_1/result.mp4"`；失败时为 null |
| events | array | 事件列表，每个元素为 EventInfo（见 4.3） |
| detection_results | array | 检测结果列表，每个元素为 DetectionInfo（见 4.4） |
| tracking_results | array | 跟踪结果列表，每个元素为 TrackingInfo（见 4.5） |
| error_message | string 或 null | 成功时为 null；失败时写清原因，如 `"模型文件不存在"` |

### 4.3 EventInfo：事件信息

| 字段 | 类型 | 说明 | 对应数据库字段 |
|---|---|---|---|
| track_id | int | DeepSORT 分配的目标 ID | events.track_id |
| confidence | float | 事件置信度 | events.confidence |
| snapshot_path | string | 报警瞬间截图路径 | events.snapshot_path |
| created_at | string | 事件时间，格式 `YYYY-MM-DD HH:mm:ss` | events.created_at |

### 4.4 DetectionInfo：检测结果

| 字段 | 类型 | 说明 | 对应数据库字段 |
|---|---|---|---|
| frame_id | int | 帧编号 | detection_results.frame_id |
| bbox_x | float | 检测框左上角 x | detection_results.bbox_x |
| bbox_y | float | 检测框左上角 y | detection_results.bbox_y |
| bbox_width | float | 检测框宽度 | detection_results.bbox_width |
| bbox_height | float | 检测框高度 | detection_results.bbox_height |
| confidence | float | 检测置信度 | detection_results.confidence |
| class_name | string | 类别名，统一为 `"falling_object"` | detection_results.class_name |

### 4.5 TrackingInfo：跟踪结果

| 字段 | 类型 | 说明 | 对应数据库字段 |
|---|---|---|---|
| track_id | int | DeepSORT 目标 ID | tracking_results.track_id |
| frame_id | int | 帧编号 | tracking_results.frame_id |
| timestamp | float | 帧时间戳（秒） | tracking_results.timestamp |
| center_x | float | 目标中心点 x | tracking_results.center_x |
| center_y | float | 目标中心点 y | tracking_results.center_y |
| bbox_x | float | 跟踪框左上角 x | tracking_results.bbox_x |
| bbox_y | float | 跟踪框左上角 y | tracking_results.bbox_y |
| bbox_width | float | 跟踪框宽度 | tracking_results.bbox_width |
| bbox_height | float | 跟踪框高度 | tracking_results.bbox_height |

## 5. 成功返回示例

```json
{
  "status": "success",
  "total_frames": 300,
  "processed_frames": 300,
  "result_video_path": "outputs/task_1/result.mp4",
  "events": [
    {
      "track_id": 3,
      "confidence": 0.82,
      "snapshot_path": "outputs/task_1/snapshots/event_1.jpg",
      "created_at": "2026-06-26 15:12:00"
    }
  ],
  "detection_results": [
    {
      "frame_id": 150,
      "bbox_x": 100,
      "bbox_y": 80,
      "bbox_width": 30,
      "bbox_height": 30,
      "confidence": 0.76,
      "class_name": "falling_object"
    }
  ],
  "tracking_results": [
    {
      "track_id": 3,
      "frame_id": 150,
      "timestamp": 5.0,
      "center_x": 115,
      "center_y": 95,
      "bbox_x": 100,
      "bbox_y": 80,
      "bbox_width": 30,
      "bbox_height": 30
    }
  ],
  "error_message": null
}
```

## 6. 失败返回示例

```json
{
  "status": "failed",
  "total_frames": 0,
  "processed_frames": 0,
  "result_video_path": null,
  "events": [],
  "detection_results": [],
  "tracking_results": [],
  "error_message": "模型文件不存在"
}
```

常见失败原因：

| error_message | 触发条件 |
|---|---|
| `"模型文件不存在"` | `models/` 目录下找不到 YOLOv11 权重文件 |
| `"视频文件不存在"` | `video_path` 路径无效 |
| `"视频读取失败"` | OpenCV 无法打开视频文件 |
| `"算法处理异常"` | 推理或跟踪过程中未预期的错误 |

## 7. 后端处理规则

| 算法输出字段 | 后端处理 |
|---|---|
| status=`"success"` | 更新 `video_tasks.status='success'` |
| status=`"failed"` | 更新 `video_tasks.status='failed'` |
| total_frames | 写入 `video_tasks.total_frames` |
| processed_frames | 写入 `video_tasks.processed_frames` |
| result_video_path | 写入 `video_tasks.result_video_path` |
| events[] | 逐条写入 `events` 表 |
| detection_results[] | 逐条写入 `detection_results` 表 |
| tracking_results[] | 逐条写入 `tracking_results` 表 |
| error_message | 写入 `video_tasks.error_message` |

## 8. 事件判定规则

算法生成 `events` 时，应同时满足以下条件（参数值来自 `settings`）：

| 条件 | 对应参数 | 默认值 |
|---|---|---|
| YOLO 检测置信度 | detect_confidence | ≥ 0.35 |
| 轨迹中下降帧占比 | downward_ratio | ≥ 70% |
| 轨迹总垂直位移 | min_vertical_distance | ≥ 80 像素 |
| 目标连续跟踪帧数 | min_track_frames | ≥ 5 |
| ROI 内轨迹点占比 | roi_required_ratio | ≥ 70% |
| 同 track_id 报警间隔 | alarm_cooldown_seconds | ≥ 10 秒 |

## 9. 接口演进说明

当前 `algorithm/pipeline.py` 实现的是**占位接口**，始终返回 `status="not_ready"`，仅用于：

- 确定函数签名和返回值结构
- 后端可以提前编写调用代码和单元测试
- 算法开发时以此为接口合同

真正接入 YOLOv11 + DeepSORT 后，占位实现替换为完整 Pipeline，**函数签名和返回结构不变**。

## 10. 测试点

- 正常 MP4 视频可返回 `status="success"` 和检测结果
- 主演示视频可返回至少 1 条事件
- 模型文件缺失时返回 `status="failed"`，后端不崩溃
- 视频文件不存在时返回 `status="failed"`，后端不崩溃
- 所有返回字段与本文档第 4 节一致
- 算法异常不导致后端 FastAPI 主线程崩溃
