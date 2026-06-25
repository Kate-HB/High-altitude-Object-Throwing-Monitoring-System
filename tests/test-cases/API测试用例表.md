# API测试用例表

> 基于 [详细API设计.md](../../详细API设计.md) 第15节测试清单扩展编写  
> 33个测试用例，覆盖认证、系统状态、视频任务、事件、统计、参数、文件、摄像头8个模块

---

## 1. 认证测试（3+2项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-AUTH-001 | `POST /api/auth/login` | 正确账号登录 | 后端已启动 | `{"username":"admin","password":"admin123"}` | 200 | `code:200`, `data.token` 非空, `data.role="admin"` |
| API-AUTH-002 | `POST /api/auth/login` | 错误密码登录 | 后端已启动 | `{"username":"admin","password":"wrong"}` | 401 | `code:401`, `message:"login failed"` |
| API-AUTH-003 | 任意受保护接口 | 无token访问 | 后端已启动 | 不带`Authorization`头 | 401 | `code:401`, 提示未登录 |
| API-AUTH-004 | `POST /api/auth/login` | 空用户名 | 后端已启动 | `{"username":"","password":"admin123"}` | 400 | `code:400`, 参数错误提示 |
| API-AUTH-005 | `POST /api/auth/login` | 空密码 | 后端已启动 | `{"username":"admin","password":""}` | 400 | `code:400`, 参数错误提示 |

---

## 2. 系统状态测试（3项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-SYS-001 | `GET /api/health` | 健康检查 | 后端已启动 | 无 | 200 | `status:"ok"`, `data.status:"running"`, `data.service`非空, `data.version`非空 |
| API-SYS-002 | `GET /api/system/status` | 系统状态（四维） | 后端已启动+登录token | Authorization头 | 200 | `data.backend.status:"running"`, `data.database.status:"connected"`, `data.algorithm`非空, `data.device`非空 |
| API-SYS-003 | `GET /api/system/status` | 模型文件缺失 | 人为移除`models/best.pt`后重启 | Authorization头 | 200 | `data.algorithm.status:"missing_model"`, `data.algorithm.model_loaded:false` |
| API-SYS-004 | `GET /api/system/status` | 无token访问 | 后端已启动 | 不带Authorization头 | 401 | `code:401` |

---

## 3. 视频任务测试（7项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-TASK-001 | `POST /api/videos/upload` | 上传正常MP4视频 | 登录token | `multipart/form-data`, file=正常MP4 | 200 | `code:200`, `data.task_id`>0, `data.status:"pending"` |
| API-TASK-002 | `POST /api/videos/upload` | 上传非视频文件 | 登录token | `multipart/form-data`, file=test.txt | 415 | `code:415`, `message:"unsupported media type"` |
| API-TASK-003 | `POST /api/tasks/{id}/analyze` | 提交ROI并启动分析 | 已上传视频，task状态=pending | `{"roi_x":100,"roi_y":50,"roi_width":400,"roi_height":300}` | 200 | `code:200`, `data.status:"running"` |
| API-TASK-004 | `POST /api/tasks/{id}/analyze` | 重复启动同一任务 | 任务已running | 同上ROI参数 | 409 | `code:409`, 冲突提示 |
| API-TASK-005 | `GET /api/tasks/{id}` | 查询任务进度 | 任务running中 | 无 | 200 | `data.processed_frames`>0, `data.progress`∈[0,100], `data.total_frames`>0 |
| API-TASK-006 | `GET /api/tasks/{id}` | 算法成功完成 | 等待任务完成 | 无 | 200 | `data.status:"success"`, `data.progress:100`, `data.result_video_path`非空 |
| API-TASK-007 | `POST /api/videos/upload` + 等待 | 损坏视频→failed | 登录token | 上传人为损坏的MP4 | 200(上传) | 任务最终`status:"failed"`, `error_message`非空 |

---

## 4. 事件测试（5项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-EVENT-001 | `GET /api/events` | 查询事件列表（分页） | 至少1条事件 | `?page=1&page_size=10` | 200 | `data.items`数组, `data.total`≥1, `data.page:1`, `data.page_size:10` |
| API-EVENT-002 | `GET /api/events/{id}` | 查询事件详情 | 已知event_id | 无 | 200 | `data.snapshot_path`非空, `data.source_task`含`result_video_path`, `data.trajectory`数组 |
| API-EVENT-003 | `PATCH /api/events/{id}/status` | 确认事件 | 事件status=unconfirmed | `{"status":"confirmed"}` | 200 | `code:200`, `data.status:"confirmed"` |
| API-EVENT-004 | `PATCH /api/events/{id}/status` | 标记误报 | 事件status=unconfirmed | `{"status":"false_alarm"}` | 200 | `code:200`, `data.status:"false_alarm"` |
| API-EVENT-005 | `PATCH /api/events/{id}/status` | 非法状态值 | 任意事件 | `{"status":"deleted"}` | 400 | `code:400`, 提示状态值不合法 |

**附加验证**：确认/误报后，`GET /api/events/{id}` 返回的 `status` 应与修改一致，且 `updated_at` 已更新。

---

## 5. 统计测试（3项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-STAT-001 | `GET /api/statistics/overview` | 空事件统计 | events表无数据 | 无 | 200 | `data.today_event_count:0`, `data.total_event_count:0`, `data.recent_events:[]`, 分布数组各项count为0 |
| API-STAT-002 | `GET /api/statistics/overview` | 新增事件后统计递增 | 新增1条事件后 | 无 | 200 | `data.total_event_count`比新增加前+1 |
| API-STAT-003 | `GET /api/statistics/overview` | 状态分布同步 | 修改事件状态后 | 无 | 200 | `data.status_distribution`中confirmed/false_alarm计数与数据库一致 |

**数据一致性验证SQL**：
```sql
-- 总事件数
SELECT COUNT(*) FROM events;
-- 今日事件数（以当天日期为准）
SELECT COUNT(*) FROM events WHERE date(created_at) = date('now','localtime');
-- 状态分布
SELECT status, COUNT(*) FROM events GROUP BY status;
```

---

## 6. 参数测试（3项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-SET-001 | `GET /api/settings` | 读取默认参数 | 数据库已初始化 | 无 | 200 | 返回6个参数，值与默认值一致：`detect_confidence:0.35`, `downward_ratio:0.7`, `min_vertical_distance:80`, `min_track_frames:5`, `roi_required_ratio:0.7`, `alarm_cooldown_seconds:10` |
| API-SET-002 | `PUT /api/settings` | 保存合法参数 | 登录token | `{"detect_confidence":0.5}` (修改1项，其余保持默认) | 200 | `code:200`, `data.detect_confidence:0.5` |
| API-SET-003 | `PUT /api/settings` | 参数超出范围 | 登录token | `{"detect_confidence":2.0}` | 400 | `code:400`, 提示参数范围 |

**附加验证**：保存后再次`GET /api/settings`，确认值持久化。重启后端后参数不丢失。

---

## 7. 文件测试（4项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-FILE-001 | `GET /api/files?path=...` | 访问结果视频 | 任务成功，result_video_path存在 | `?path=outputs/result_1.mp4` | 200 | Content-Type为video/mp4，响应体为视频二进制流 |
| API-FILE-002 | `GET /api/files?path=...` | 访问事件截图 | 事件有snapshot_path | `?path=events/snapshots/event_1.jpg` | 200 | Content-Type为image/jpeg |
| API-FILE-003 | `GET /api/files?path=...` | 访问不存在文件 | 无 | `?path=outputs/nonexistent.mp4` | 404 | `code:404`, 提示文件不存在 |
| API-FILE-004 | `GET /api/files?path=...` | 路径穿越攻击 | 登录token | `?path=../secrets.txt` | 400 | `code:400`, 拒绝非法路径 |

---

## 8. 摄像头测试（5项）

| 编号 | 接口 | 测试项 | 前置条件 | 输入 | 预期HTTP状态 | 预期响应 |
|---|---|---|---|---|---|---|
| API-CAM-001 | `POST /api/camera/start` | 启动摄像头 | 本机有摄像头，登录token | `{"camera_index":0}` | 200 | `data.status:"running"`, `data.camera_index:0` |
| API-CAM-002 | `GET /api/camera/status` | 查询运行中状态 | 摄像头已启动 | 无 | 200 | `data.status:"running"` |
| API-CAM-003 | `GET /api/camera/stream` | 获取MJPEG流 | 摄像头已启动 | 浏览器`<img>`标签访问 | 200 | Content-Type:`multipart/x-mixed-replace`，画面连续 |
| API-CAM-004 | `POST /api/camera/stop` | 停止摄像头 | 摄像头running中 | 无 | 200 | `data.status:"stopped"` |
| API-CAM-005 | `POST /api/camera/start` | 摄像头被占用 | 摄像头已被其他程序占用 | `{"camera_index":0}` | 503 | `code:503`, 提示摄像头不可用 |

---

## 9. 测试执行计划

| 阶段 | 日期 | 用例范围 | 依赖 |
|---|---|---|---|
| 第一阶段 | 6/25 | API-AUTH-001~005, API-SYS-001~004 | 登录接口、系统接口已完成 |
| 第二阶段 | 6/26 | API-TASK-001~003 | 上传接口已完成 |
| 第三阶段 | 6/28 | API-TASK-004~007, API-EVENT-001 | 算法集成、事件入库完成 |
| 第四阶段 | 6/29 | API-EVENT-002~005, API-FILE-001~004 | 事件详情、文件接口完成 |
| 第五阶段 | 6/30 | API-STAT-001~003, API-SET-001~003, API-CAM-001~005 | 统计、参数、摄像头接口完成 |
| 回归 | 7/1 | 全部33项 | 全部接口冻结 |

---

## 10. 用例统计

| 模块 | 用例数 | 正常流程 | 异常流程 | 边界条件 |
|---|---|---|---|---|
| 认证 | 5 | 1 | 2 | 2 |
| 系统状态 | 4 | 2 | 1 | 1 |
| 视频任务 | 7 | 3 | 3 | 1 |
| 事件 | 5 | 2 | 1 | 2 |
| 统计 | 3 | 1 | 0 | 2 |
| 参数 | 3 | 1 | 1 | 1 |
| 文件 | 4 | 2 | 2 | 0 |
| 摄像头 | 5 | 3 | 1 | 1 |
| **合计** | **36** | **15** | **11** | **10** |
