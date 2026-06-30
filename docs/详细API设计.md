# 高空抛物监测系统详细API设计

## 1. 文档说明

本文档是高空抛物监测系统的详细 API 设计文档，用于统一前端、后端、算法和测试之间的接口约定。

《详细需求分析》第 10 节已经定义接口范围，本文档在其基础上补充：

- URL 与 HTTP 方法。
- 请求参数。
- 响应字段。
- 错误码。
- 调用页面。
- 数据表影响。
- 联调和测试点。

本文档不新增需求范围，不改变系统架构。接口字段以《详细需求分析》第 8.4 节数据建模为准。

## 2. 通用接口约定

### 2.1 基础地址

| 项目 | 内容 |
|---|---|
| 后端服务地址 | `http://127.0.0.1:8000` |
| API 基础路径 | `http://127.0.0.1:8000/api` |
| 接口数据格式 | JSON |
| 文件上传格式 | `multipart/form-data` |
| 字符编码 | UTF-8 |
| 时间格式 | `YYYY-MM-DD HH:mm:ss` |

### 2.2 鉴权方式

系统只设置一个管理员账号：

| 项目 | 内容 |
|---|---|
| 用户名 | `admin` |
| 密码 | `admin123` |
| 用户角色 | `admin` |
| 用户表 | 不建表 |
| token | 登录成功后由后端返回简单 token |

除登录接口、健康检查接口、摄像头 MJPEG 流接口外，其余接口默认需要携带 token。

请求头：

```http
Authorization: Bearer <token>
```

token 缺失、错误或过期时，后端返回 `401`。

### 2.3 通用成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | integer | 是 | 业务状态码，成功为 200 |
| message | string | 是 | 响应说明 |
| data | object / array / null | 是 | 实际数据 |

### 2.4 通用失败响应

```json
{
  "code": 400,
  "message": "bad request",
  "detail": "视频格式不支持"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | integer | 是 | 错误码 |
| message | string | 是 | 错误类型 |
| detail | string / object | 是 | 具体错误原因 |

### 2.5 分页约定

事件列表等分页接口统一使用以下字段：

请求参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| page | integer | 1 | 当前页码，从 1 开始 |
| page_size | integer | 10 | 每页数量 |

响应结构：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

## 3. 错误码设计

| HTTP 状态码 | 业务 code | 场景 | 前端处理 |
|---|---:|---|---|
| 200 | 200 | 请求成功 | 正常展示 |
| 400 | 400 | 参数错误、格式错误 | 页面提示错误原因 |
| 401 | 401 | 未登录、token 无效 | 跳转登录页 |
| 404 | 404 | 任务、事件、文件不存在 | 显示不存在提示 |
| 409 | 409 | 摄像头已打开、任务状态冲突 | 显示冲突提示 |
| 413 | 413 | 文件过大 | 提示压缩或更换视频 |
| 415 | 415 | 文件类型不支持 | 提示上传支持格式 |
| 500 | 500 | 服务内部异常 | 显示系统异常 |
| 503 | 503 | 算法模型缺失、摄像头不可用 | 显示模块不可用 |

## 4. 认证接口

### 4.1 管理员登录

| 项目 | 内容 |
|---|---|
| 接口名称 | 管理员登录 |
| URL | `/api/auth/login` |
| Method | `POST` |
| Content-Type | `application/json` |
| 是否鉴权 | 否 |
| 调用页面 | 管理员登录页 |
| 数据表影响 | 无，账号硬编码校验 |

请求体：

```json
{
  "username": "admin",
  "password": "admin123"
}
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | string | 是 | 管理员账号 |
| password | string | 是 | 管理员密码 |

成功响应：

```json
{
  "code": 200,
  "message": "login success",
  "data": {
    "token": "simple-admin-token",
    "username": "admin",
    "role": "admin"
  }
}
```

失败响应：

```json
{
  "code": 401,
  "message": "login failed",
  "detail": "账号或密码错误"
}
```

测试点：

- 输入 `admin/admin123` 登录成功。
- 输入错误账号登录失败。
- 输入错误密码登录失败。
- 用户名或密码为空时返回参数错误。

## 5. 系统状态接口

### 5.1 健康检查

| 项目 | 内容 |
|---|---|
| 接口名称 | 健康检查 |
| URL | `/api/health` |
| Method | `GET` |
| 是否鉴权 | 否 |
| 调用页面 | 系统首页、启动检查 |
| 数据表影响 | 无 |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "running",
    "service": "backend",
    "version": "0.1.0",
    "time": "2026-06-24 15:00:00"
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| status | string | 后端状态，`running` 表示正常 |
| service | string | 服务名称 |
| version | string | 系统版本 |
| time | string | 当前服务时间 |

测试点：

- 后端启动后接口返回 200。
- 首页能显示后端在线。

### 5.2 系统状态

| 项目 | 内容 |
|---|---|
| 接口名称 | 系统状态 |
| URL | `/api/system/status` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 系统首页 |
| 数据表影响 | 可读取数据库连接状态，不写入 |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "backend": {
      "status": "running",
      "message": "后端服务正常"
    },
    "database": {
      "status": "connected",
      "message": "SQLite连接正常"
    },
    "algorithm": {
      "status": "ready",
      "model_loaded": true,
      "message": "算法模块可用"
    },
    "device": {
      "device_type": "gpu",
      "cuda_available": true,
      "gpu_name": "NVIDIA GeForce RTX 3050",
      "cpu_fallback": true
    }
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| backend.status | string | `running` / `error` |
| database.status | string | `connected` / `error` |
| algorithm.status | string | `ready` / `missing_model` / `error` |
| algorithm.model_loaded | boolean | 模型是否加载 |
| device.device_type | string | `gpu` / `cpu` |
| device.cuda_available | boolean | CUDA 是否可用 |
| device.gpu_name | string | GPU 名称，无 GPU 时为空 |
| device.cpu_fallback | boolean | 是否支持 CPU 降级 |

测试点：

- 数据库正常时返回 `connected`。
- 模型缺失时返回 `missing_model`。
- 无 GPU 设备时允许 `device_type=cpu`。

## 6. 视频上传与任务接口

### 6.1 上传视频并创建分析任务

| 项目 | 内容 |
|---|---|
| 接口名称 | 视频上传与任务创建 |
| URL | `/api/videos/upload` |
| Method | `POST` |
| Content-Type | `multipart/form-data` |
| 是否鉴权 | 是 |
| 调用页面 | 视频分析页 |
| 写入数据表 | `video_tasks` |
| 文件写入 | `uploads/` |

说明：上传视频与创建任务合并为一个接口。该接口只负责保存视频并创建 `video_tasks` 记录，任务初始状态为 `pending`。ROI 统一通过 `POST /api/tasks/{task_id}/analyze` 提交，并由该接口启动后台分析。

请求参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| file | file | 是 | 无 | 上传视频文件 |

支持视频格式：

- `.mp4`
- `.avi`
- `.mov`
- `.mkv`

成功响应：

```json
{
  "code": 200,
  "message": "upload success",
  "data": {
    "task_id": 1,
    "status": "pending",
    "source_type": "upload",
    "source_path": "uploads/demo.mp4",
    "created_at": "2026-06-24 15:10:00"
  }
}
```

`video_tasks` 写入字段：

| 字段 | 写入值 |
|---|---|
| source_type | `upload` |
| source_path | 上传视频保存路径 |
| status | `pending` |
| total_frames | 后端读取视频后写入 |
| processed_frames | 初始为 0 |
| roi_x / roi_y / roi_width / roi_height | 初始为空，分析接口提交后写入 |
| created_at / updated_at | 当前时间 |

失败响应示例：

```json
{
  "code": 415,
  "message": "unsupported media type",
  "detail": "仅支持 mp4、avi、mov、mkv 视频"
}
```

测试点：

- 正常 MP4 上传成功。
- 上传非视频文件失败。
- 上传损坏视频后任务进入 `failed`。
- 上传后任务保持 `pending`，不立即启动分析。
- ROI 统一由 `POST /api/tasks/{task_id}/analyze` 提交。

### 6.2 提交 ROI 并启动分析

| 项目 | 内容 |
|---|---|
| 接口名称 | 提交 ROI 并启动分析 |
| URL | `/api/tasks/{task_id}/analyze` |
| Method | `POST` |
| Content-Type | `application/json` |
| 是否鉴权 | 是 |
| 调用页面 | 视频分析页 |
| 读取数据表 | `video_tasks`、`system_settings` |
| 更新数据表 | `video_tasks` |

使用场景：前端先上传视频并显示首帧，管理员在首帧上绘制 ROI 后，再调用该接口启动算法分析。该接口解决“上传在前、ROI 绘制在后”的联调流程。

路径参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_id | integer | 是 | 视频分析任务 ID |

请求体：

```json
{
  "roi_x": 100,
  "roi_y": 50,
  "roi_width": 400,
  "roi_height": 300,
  "detect_confidence": 0.35
}
```

请求字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| roi_x | integer | 否 | 0 | ROI 左上角 x |
| roi_y | integer | 否 | 0 | ROI 左上角 y |
| roi_width | integer | 否 | 视频宽度 | ROI 宽度 |
| roi_height | integer | 否 | 视频高度 | ROI 高度 |
| detect_confidence | number | 否 | 系统参数值 | 检测置信度阈值 |

成功响应：

```json
{
  "code": 200,
  "message": "analysis started",
  "data": {
    "task_id": 1,
    "status": "running",
    "roi": {
      "x": 100,
      "y": 50,
      "width": 400,
      "height": 300
    },
    "updated_at": "2026-06-24 15:15:00"
  }
}
```

失败响应：

```json
{
  "code": 409,
  "message": "task conflict",
  "detail": "任务已经开始分析，不能重复启动"
}
```

测试点：

- 上传后绘制 ROI，再启动分析成功。
- 重复启动同一任务返回 409。
- 任务不存在返回 404。
- ROI 超出画面范围时返回 400 或自动限制到有效范围。

### 6.3 查询分析任务

| 项目 | 内容 |
|---|---|
| 接口名称 | 查询分析任务 |
| URL | `/api/tasks/{task_id}` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 视频分析页 |
| 读取数据表 | `video_tasks`、`events` |

路径参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_id | integer | 是 | 视频分析任务 ID |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "source_type": "upload",
    "source_path": "uploads/demo.mp4",
    "status": "running",
    "total_frames": 300,
    "processed_frames": 120,
    "progress": 40.0,
    "roi": {
      "x": 100,
      "y": 50,
      "width": 400,
      "height": 300
    },
    "result_video_path": null,
    "error_message": null,
    "events": [],
    "created_at": "2026-06-24 15:10:00",
    "updated_at": "2026-06-24 15:11:00"
  }
}
```

任务状态：

| 状态 | 说明 |
|---|---|
| pending | 已创建，等待分析 |
| running | 正在分析 |
| success | 分析完成 |
| failed | 分析失败 |

完成后响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "success",
    "total_frames": 300,
    "processed_frames": 300,
    "progress": 100.0,
    "result_video_path": "outputs/result_1.mp4",
    "error_message": null,
    "events": [
      {
        "id": 1,
        "track_id": 3,
        "confidence": 0.82,
        "status": "unconfirmed",
        "snapshot_path": "events/snapshots/event_1.jpg",
        "created_at": "2026-06-24 15:12:00"
      }
    ]
  }
}
```

失败响应：

```json
{
  "code": 404,
  "message": "not found",
  "detail": "任务不存在"
}
```

测试点：

- 上传后能查询到 `pending` 或 `running`。
- 分析中 `processed_frames` 增加。
- 分析完成后 `progress=100`。
- 分析失败时返回 `error_message`。

## 7. 事件报警接口

### 7.1 查询事件列表

| 项目 | 内容 |
|---|---|
| 接口名称 | 查询事件列表 |
| URL | `/api/events` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 报警中心页、历史事件页、数据看板 |
| 读取数据表 | `events` |

查询参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| status | string | 否 | 全部 | `unconfirmed` / `confirmed` / `false_alarm` |
| start_time | string | 否 | 无 | 开始时间 |
| end_time | string | 否 | 无 | 结束时间 |
| min_confidence | number | 否 | 无 | 最低置信度 |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "video_task_id": 1,
        "track_id": 3,
        "confidence": 0.82,
        "status": "unconfirmed",
        "snapshot_path": "events/snapshots/event_1.jpg",
        "created_at": "2026-06-24 15:12:00",
        "updated_at": "2026-06-24 15:12:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

事件状态：

| 状态 | 说明 |
|---|---|
| unconfirmed | 未确认，算法刚触发 |
| confirmed | 管理员确认 |
| false_alarm | 管理员标记为误报 |

测试点：

- 无事件时返回空列表。
- 按状态筛选正确。
- 按时间范围筛选正确。
- 按置信度筛选正确。

### 7.2 查询事件详情

| 项目 | 内容 |
|---|---|
| 接口名称 | 查询事件详情 |
| URL | `/api/events/{event_id}` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 报警中心页、历史事件页 |
| 读取数据表 | `events`、`video_tasks`、`tracking_results` |

路径参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| event_id | integer | 是 | 事件 ID |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "video_task_id": 1,
    "track_id": 3,
    "confidence": 0.82,
    "status": "unconfirmed",
    "snapshot_path": "events/snapshots/event_1.jpg",
    "created_at": "2026-06-24 15:12:00",
    "updated_at": "2026-06-24 15:12:00",
    "source_task": {
      "id": 1,
      "source_path": "uploads/demo.mp4",
      "source_type": "upload",
      "result_video_path": "outputs/result_1.mp4"
    },
    "trajectory": [
      {
        "frame_id": 10,
        "timestamp": 0.4,
        "center_x": 120,
        "center_y": 80
      },
      {
        "frame_id": 11,
        "timestamp": 0.44,
        "center_x": 123,
        "center_y": 96
      }
    ]
  }
}
```

失败响应：

```json
{
  "code": 404,
  "message": "not found",
  "detail": "事件不存在"
}
```

测试点：

- 点击事件详情能返回截图、视频、轨迹。
- 事件不存在时返回 404。
- 截图或视频文件缺失时，接口仍返回事件信息，由前端展示缺失提示。

### 7.3 更新事件状态

| 项目 | 内容 |
|---|---|
| 接口名称 | 更新事件状态 |
| URL | `/api/events/{event_id}/status` |
| Method | `PATCH` |
| Content-Type | `application/json` |
| 是否鉴权 | 是 |
| 调用页面 | 报警中心页、历史事件页 |
| 更新数据表 | `events` |

请求体：

```json
{
  "status": "confirmed"
}
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| status | string | 是 | `unconfirmed` / `confirmed` / `false_alarm` |

成功响应：

```json
{
  "code": 200,
  "message": "status updated",
  "data": {
    "id": 1,
    "status": "confirmed",
    "updated_at": "2026-06-24 15:20:00"
  }
}
```

失败响应：

```json
{
  "code": 400,
  "message": "bad request",
  "detail": "事件状态值不合法"
}
```

测试点：

- 未确认事件可改为已确认。
- 未确认事件可改为误报。
- 非法状态值返回 400。
- 状态更新后历史事件页和数据看板同步变化。

## 8. 数据看板统计接口

### 8.1 获取统计概览

| 项目 | 内容 |
|---|---|
| 接口名称 | 数据看板统计 |
| URL | `/api/statistics/overview` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 系统首页、数据看板页 |
| 读取数据表 | `events` |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "today_event_count": 2,
    "total_event_count": 15,
    "recent_events": [
      {
        "id": 15,
        "confidence": 0.78,
        "status": "unconfirmed",
        "created_at": "2026-06-24 16:10:00"
      }
    ],
    "daily_trend": [
      {
        "date": "2026-06-24",
        "count": 2
      }
    ],
    "confidence_distribution": [
      {
        "range": "0.35-0.5",
        "count": 3
      },
      {
        "range": "0.5-0.7",
        "count": 5
      },
      {
        "range": "0.7-1.0",
        "count": 7
      }
    ],
    "status_distribution": [
      {
        "status": "unconfirmed",
        "count": 4
      },
      {
        "status": "confirmed",
        "count": 8
      },
      {
        "status": "false_alarm",
        "count": 3
      }
    ]
  }
}
```

统计规则：

| 统计项 | 来源 | 规则 |
|---|---|---|
| 今日报警数 | `events` | `created_at` 为当天 |
| 累计事件数 | `events` | 总记录数 |
| 最近事件 | `events` | 按 `created_at` 倒序取前 5 条 |
| 日期趋势 | `events` | 按日期分组 |
| 置信度分布 | `events` | 默认按 `0.35-0.5`、`0.5-0.7`、`0.7-1.0`；若检测阈值被修改，可按实际阈值动态调整第一档起点 |
| 状态分布 | `events` | 按 `status` 分组 |

测试点：

- `events` 为空时所有数量为 0。
- 新增事件后累计事件数增加。
- 更新事件状态后状态分布变化。
- 页面展示值与数据库查询结果一致。

## 9. 参数配置接口

### 9.1 读取系统参数

| 项目 | 内容 |
|---|---|
| 接口名称 | 读取系统参数 |
| URL | `/api/settings` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 参数设置页、视频分析页 |
| 读取数据表 | `system_settings` |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "detect_confidence": 0.35,
    "downward_ratio": 0.7,
    "min_vertical_distance": 80,
    "min_track_frames": 5,
    "roi_required_ratio": 0.7,
    "alarm_cooldown_seconds": 10,
    "updated_at": "2026-06-24 15:00:00"
  }
}
```

字段说明：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| detect_confidence | number | 0.35 | YOLO 检测置信度阈值 |
| downward_ratio | number | 0.7 | 连续下降帧占比阈值 |
| min_vertical_distance | integer | 80 | 最小垂直位移 |
| min_track_frames | integer | 5 | 最小连续跟踪帧数 |
| roi_required_ratio | number | 0.7 | ROI 内轨迹点占比 |
| alarm_cooldown_seconds | integer | 10 | 报警冷却时间 |

测试点：

- 初始化数据库后能读取默认参数。
- 参数字段完整。

### 9.2 保存系统参数

| 项目 | 内容 |
|---|---|
| 接口名称 | 保存系统参数 |
| URL | `/api/settings` |
| Method | `PUT` |
| Content-Type | `application/json` |
| 是否鉴权 | 是 |
| 调用页面 | 参数设置页 |
| 更新数据表 | `system_settings` |

请求体：

```json
{
  "detect_confidence": 0.4,
  "downward_ratio": 0.7,
  "min_vertical_distance": 90,
  "min_track_frames": 5,
  "roi_required_ratio": 0.7,
  "alarm_cooldown_seconds": 10
}
```

参数范围建议：

| 字段 | 类型 | 建议范围 |
|---|---|---|
| detect_confidence | number | 0.1 到 1.0 |
| downward_ratio | number | 0.5 到 1.0 |
| min_vertical_distance | integer | 10 到 500 |
| min_track_frames | integer | 1 到 100 |
| roi_required_ratio | number | 0 到 1.0 |
| alarm_cooldown_seconds | integer | 0 到 300 |

成功响应：

```json
{
  "code": 200,
  "message": "settings updated",
  "data": {
    "detect_confidence": 0.4,
    "downward_ratio": 0.7,
    "min_vertical_distance": 90,
    "min_track_frames": 5,
    "roi_required_ratio": 0.7,
    "alarm_cooldown_seconds": 10,
    "updated_at": "2026-06-24 15:30:00"
  }
}
```

失败响应：

```json
{
  "code": 400,
  "message": "bad request",
  "detail": "detect_confidence 必须在 0.1 到 1.0 之间"
}
```

测试点：

- 参数保存成功。
- 保存后再次读取值一致。
- 非法参数返回 400。
- 参数变化不影响已完成历史事件。

## 10. 文件访问接口

### 10.1 访问本地文件

| 项目 | 内容 |
|---|---|
| 接口名称 | 文件访问 |
| URL | `/api/files` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 视频分析页、报警中心页、历史事件页 |
| 读取文件 | `uploads/`、`outputs/`、`events/snapshots/` |

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| path | string | 是 | 文件相对路径 |

请求示例：

```http
GET /api/files?path=outputs/result_1.mp4
```

允许访问目录：

| 目录 | 说明 |
|---|---|
| `uploads/` | 上传原视频 |
| `outputs/` | 结果视频 |
| `events/snapshots/` | 事件截图 |

安全限制：

- 只能访问项目允许目录。
- 禁止访问绝对路径。
- 禁止使用 `../` 路径穿越。
- 文件不存在返回 404。

失败响应：

```json
{
  "code": 404,
  "message": "not found",
  "detail": "文件不存在"
}
```

测试点：

- 结果视频可播放。
- 事件截图可查看。
- 不存在文件返回 404。
- 非法路径返回 400。

## 11. 摄像头实时检测接口

### 11.1 启动摄像头

| 项目 | 内容 |
|---|---|
| 接口名称 | 启动摄像头 |
| URL | `/api/camera/start` |
| Method | `POST` |
| 是否鉴权 | 是 |
| 调用页面 | 实时监控页 |
| 数据表影响 | 无 |

请求体：

```json
{
  "camera_index": 0,
  "width": 640,
  "height": 480
}
```

请求字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| camera_index | integer | 否 | 0 | 本机摄像头编号 |
| width | integer | 否 | 640 | 画面宽度 |
| height | integer | 否 | 480 | 画面高度 |

成功响应：

```json
{
  "code": 200,
  "message": "camera started",
  "data": {
    "status": "running",
    "camera_index": 0,
    "width": 640,
    "height": 480,
    "fps": 15
  }
}
```

失败响应：

```json
{
  "code": 503,
  "message": "camera unavailable",
  "detail": "摄像头不可用或被占用"
}
```

测试点：

- 摄像头可正常打开。
- 摄像头被占用时返回明确错误。
- 重复启动时不导致程序崩溃。

### 11.2 停止摄像头

| 项目 | 内容 |
|---|---|
| 接口名称 | 停止摄像头 |
| URL | `/api/camera/stop` |
| Method | `POST` |
| 是否鉴权 | 是 |
| 调用页面 | 实时监控页 |
| 数据表影响 | 无 |

成功响应：

```json
{
  "code": 200,
  "message": "camera stopped",
  "data": {
    "status": "stopped"
  }
}
```

测试点：

- 停止后摄像头资源释放。
- 再次启动摄像头成功。

### 11.3 查询摄像头状态

| 项目 | 内容 |
|---|---|
| 接口名称 | 查询摄像头状态 |
| URL | `/api/camera/status` |
| Method | `GET` |
| 是否鉴权 | 是 |
| 调用页面 | 实时监控页 |
| 数据表影响 | 无 |

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "running",
    "camera_index": 0,
    "width": 640,
    "height": 480,
    "fps": 15
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| status | string | `running` / `stopped` / `error` |
| camera_index | integer | 摄像头编号 |
| width | integer | 画面宽度 |
| height | integer | 画面高度 |
| fps | number | 当前或目标帧率 |

测试点：

- 摄像头未启动时返回 `stopped`。
- 摄像头启动后返回 `running`。
- 摄像头异常时返回 `error` 和错误说明。

### 11.4 获取摄像头实时画面

| 项目 | 内容 |
|---|---|
| 接口名称 | 摄像头实时画面 |
| URL | `/api/camera/stream` |
| Method | `GET` |
| 返回类型 | `multipart/x-mixed-replace` |
| 是否鉴权 | 可不鉴权，便于 `<img>` 展示 |
| 调用页面 | 实时监控页 |
| 数据表影响 | 无 |

前端调用：

```html
<img src="http://127.0.0.1:8000/api/camera/stream" />
```

返回内容：

- MJPEG 视频流。
- 每帧画面绘制 YOLOv11 检测框。
- 不要求 DeepSORT 跟踪。
- 不要求报警。
- 不要求写入 `events`。

测试点：

- 页面能显示实时画面。
- 关闭摄像头后画面停止。
- 摄像头异常时前端显示错误提示。

## 12. 后端与算法 Pipeline 接口

### 12.1 调用函数

后端调用算法模块统一使用以下函数：

```python
run_video_analysis(
    video_path,
    output_dir,
    roi,
    settings
)
```

### 12.2 输入参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| video_path | string | 是 | 原视频路径 |
| output_dir | string | 是 | 结果视频和截图输出目录 |
| roi | dict | 是 | ROI 区域 |
| settings | dict | 是 | 检测和报警参数 |

`roi` 示例：

```json
{
  "x": 100,
  "y": 50,
  "width": 400,
  "height": 300
}
```

`settings` 示例：

```json
{
  "detect_confidence": 0.35,
  "downward_ratio": 0.7,
  "min_vertical_distance": 80,
  "min_track_frames": 5,
  "roi_required_ratio": 0.7,
  "alarm_cooldown_seconds": 10
}
```

### 12.3 输出结果

成功返回：

```json
{
  "status": "success",
  "total_frames": 300,
  "processed_frames": 300,
  "result_video_path": "outputs/result_1.mp4",
  "events": [
    {
      "track_id": 3,
      "confidence": 0.82,
      "snapshot_path": "events/snapshots/event_1.jpg",
      "created_at": "2026-06-24 15:12:00"
    }
  ],
  "detection_results": [
    {
      "frame_id": 10,
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
      "frame_id": 10,
      "timestamp": 0.4,
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

失败返回：

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

### 12.4 后端处理规则

| 算法输出 | 后端处理 |
|---|---|
| `status=success` | 更新 `video_tasks.status=success` |
| `status=failed` | 更新 `video_tasks.status=failed` |
| `total_frames` | 写入 `video_tasks.total_frames` |
| `processed_frames` | 写入 `video_tasks.processed_frames` |
| `result_video_path` | 写入 `video_tasks.result_video_path` |
| `events` | 写入 `events` |
| `detection_results` | 写入 `detection_results` |
| `tracking_results` | 写入 `tracking_results` |
| `error_message` | 写入 `video_tasks.error_message` |

### 12.5 算法事件判定规则

算法生成疑似事件时，至少应满足以下规则：

| 条件 | 默认值 |
|---|---|
| 检测置信度 | ≥ 0.35 |
| 连续下降帧占比 | ≥ 70% |
| 最小垂直位移 | ≥ 80 像素 |
| 最小连续跟踪帧数 | ≥ 5 |
| ROI 内轨迹点占比 | ≥ 70% |
| 报警冷却 | 10 秒 |

测试点：

- 正常视频可返回检测结果。
- 主演示视频可返回事件。
- 模型缺失时返回 `failed`。
- 算法异常不导致后端崩溃。

## 13. 页面与接口调用关系

| 页面 | 调用接口 | 主要用途 |
|---|---|---|
| 管理员登录页 | `POST /api/auth/login` | 登录系统 |
| 系统首页 | `GET /api/health`、`GET /api/system/status`、`GET /api/statistics/overview` | 显示服务状态和核心统计 |
| 视频分析页 | `POST /api/videos/upload`、`POST /api/tasks/{task_id}/analyze`、`GET /api/tasks/{task_id}`、`GET /api/files?path=` | 上传视频、提交 ROI、查询进度、播放结果 |
| 实时监控页 | `POST /api/camera/start`、`GET /api/camera/status`、`GET /api/camera/stream`、`POST /api/camera/stop` | 摄像头辅演示 |
| 报警中心页 | `GET /api/events`、`GET /api/events/{event_id}`、`PATCH /api/events/{event_id}/status` | 查看和处理报警 |
| 历史事件页 | `GET /api/events`、`GET /api/events/{event_id}`、`GET /api/files?path=` | 筛选、详情、回放 |
| 数据看板页 | `GET /api/statistics/overview` | 图表统计 |
| 参数设置页 | `GET /api/settings`、`PUT /api/settings` | 参数读取和保存 |

## 14. 数据表影响关系

| 接口 | 读取数据表 | 写入 / 更新数据表 |
|---|---|---|
| `POST /api/auth/login` | 无 | 无 |
| `GET /api/health` | 无 | 无 |
| `GET /api/system/status` | 数据库连接状态 | 无 |
| `POST /api/videos/upload` | `system_settings` | `video_tasks` |
| `POST /api/tasks/{task_id}/analyze` | `video_tasks`、`system_settings` | `video_tasks` |
| `GET /api/tasks/{task_id}` | `video_tasks`、`events` | 无 |
| `GET /api/events` | `events` | 无 |
| `GET /api/events/{event_id}` | `events`、`video_tasks`、`tracking_results` | 无 |
| `PATCH /api/events/{event_id}/status` | `events` | `events` |
| `GET /api/statistics/overview` | `events` | 无 |
| `GET /api/settings` | `system_settings` | 无 |
| `PUT /api/settings` | `system_settings` | `system_settings` |
| `GET /api/files?path=` | 无 | 无 |
| `POST /api/camera/start` | 无 | 无 |
| `POST /api/camera/stop` | 无 | 无 |
| `GET /api/camera/status` | 无 | 无 |
| `GET /api/camera/stream` | 无 | 无 |

## 15. 接口测试清单

### 15.1 认证测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-AUTH-001 | 正确账号登录 | 返回 token |
| API-AUTH-002 | 错误账号登录 | 返回 401 |
| API-AUTH-003 | 未携带 token 调用受保护接口 | 返回 401 |

### 15.2 系统状态测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-SYS-001 | 健康检查 | 返回 `running` |
| API-SYS-002 | 系统状态 | 返回后端、数据库、算法、设备状态 |
| API-SYS-003 | 模型缺失 | algorithm 返回 `missing_model` 或错误说明 |

### 15.3 视频任务测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-TASK-001 | 上传正常视频 | 创建任务 |
| API-TASK-002 | 上传非视频文件 | 返回 415 |
| API-TASK-003 | 提交 ROI 并启动分析 | 任务变为 `running` |
| API-TASK-004 | 重复启动同一任务 | 返回 409 |
| API-TASK-005 | 查询任务进度 | 返回 `processed_frames` 和 `progress` |
| API-TASK-006 | 算法成功 | 任务变为 `success` |
| API-TASK-007 | 算法失败 | 任务变为 `failed` 并有错误原因 |

### 15.4 事件测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-EVENT-001 | 查询事件列表 | 返回分页数据 |
| API-EVENT-002 | 查询事件详情 | 返回截图、结果视频和轨迹 |
| API-EVENT-003 | 确认事件 | 状态变为 `confirmed` |
| API-EVENT-004 | 标记误报 | 状态变为 `false_alarm` |
| API-EVENT-005 | 非法事件状态 | 返回 400 |

### 15.5 统计测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-STAT-001 | events 为空 | 统计值为 0 |
| API-STAT-002 | 新增事件后统计 | 累计事件数增加 |
| API-STAT-003 | 更新事件状态 | 状态分布同步变化 |

### 15.6 参数测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-SET-001 | 读取默认参数 | 返回 6 个核心参数 |
| API-SET-002 | 保存合法参数 | 保存成功 |
| API-SET-003 | 保存非法参数 | 返回 400 |

### 15.7 文件测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-FILE-001 | 访问结果视频 | 可播放 |
| API-FILE-002 | 访问截图 | 可显示 |
| API-FILE-003 | 访问不存在文件 | 返回 404 |
| API-FILE-004 | 使用非法路径 | 返回 400 |

### 15.8 摄像头测试

| 编号 | 测试项 | 预期结果 |
|---|---|---|
| API-CAM-001 | 启动摄像头 | 返回 `running` |
| API-CAM-002 | 查询摄像头状态 | 返回 `running` 或 `stopped` |
| API-CAM-003 | 获取 MJPEG 流 | 页面可显示实时画面 |
| API-CAM-004 | 停止摄像头 | 返回 `stopped` |
| API-CAM-005 | 摄像头被占用 | 返回 503 |

## 16. 联调优先级

| 优先级 | 接口 | 原因 |
|---|---|---|
| P0 | `POST /api/auth/login` | 所有页面入口 |
| P0 | `POST /api/videos/upload` | 主演示核心入口 |
| P0 | `POST /api/tasks/{task_id}/analyze` | ROI 提交和启动分析 |
| P0 | `GET /api/tasks/{task_id}` | 主演示进度和结果展示 |
| P0 | `GET /api/events` | 报警、历史、看板依赖 |
| P0 | `GET /api/files?path=` | 结果视频和截图展示 |
| P1 | `PATCH /api/events/{event_id}/status` | 事件处置演示 |
| P1 | `GET /api/statistics/overview` | 数据看板 |
| P1 | `GET /api/settings`、`PUT /api/settings` | 参数设置 |
| P2 | `POST /api/camera/start`、`GET /api/camera/status`、`GET /api/camera/stream`、`POST /api/camera/stop` | 摄像头辅演示 |

## 17. 结论

本文档将需求分析中的接口范围细化为可开发、可联调、可测试的 API 设计。

前端开发应以本文档确定页面调用方式和字段名称；后端开发应以本文档实现 FastAPI 接口、数据库读写和文件访问；算法开发应以 Pipeline 接口输出结构化结果；测试人员应以接口测试清单设计测试报告内容。
