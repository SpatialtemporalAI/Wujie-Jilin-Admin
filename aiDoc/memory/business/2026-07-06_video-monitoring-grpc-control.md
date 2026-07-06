# 视频监控 gRPC 启停控制（对接机器人 middleware）

## 需求描述

平台侧新增对**视频监控的启停控制**：HTTP 接口 → gRPC 客户端 → 调用**对应机器人 middleware 服务**下发启动 / 停止视频监控指令。

运营监控页已有「视频监控」Tab，但前端 `video-player.vue` 是空壳（`streamUrl` 恒为 null），后端此前无任何视频控制能力；`protos/` 下也无视频相关 proto，需新建契约。

## 状态

已完成（后端 + 前端 API/类型；不含视频流实际渲染）

## 关键决策（已与用户确认）

1. **RPC 形态**：单一 RPC `NotifyVideoMonitoringChanged(robot_id, enabled)`，与 voice/speed/battery 的 `NotifyXxxChanged` 约定一致。
2. **Start 参数**：仅 `robot_id`（流地址 / 摄像头编号 / 清晰度等由 middleware 自治，平台不下发）。
3. **调用语义**：**实时控制** fire-and-forget——失败直接回 fail，**不入 `grpc_retry_task`**、**不落库**。与 `test_wake_word` / `test_tts` / task `run_now` 一致（区别于 speed/voice 的「持久化配置 + 重试」语义）。
4. **范围**：后端 proto + client + service schema + endpoint，前端 API + 类型；**不含**视频流渲染。

> 对端契约：middleware 团队需按本 proto 实现 `VideoMonitoringService.NotifyVideoMonitoringChanged` 的 server 端。

## 涉及范围

### 后端

- **新 proto** `backend/grpc/protos/config/video.proto`（submodule 内）
  - package `wujie.scene.video_monitoring.v1`，service `VideoMonitoringService`
  - `VideoMonitoringChangedRequest { int64 robot_id; bool enabled }` / `VideoMonitoringChangedResponse { bool success; string message }`
- **生成 stub** `backend/grpc/generated/config/video_pb2.py` / `video_pb2_grpc.py`（`uv run python main.py`，经路径桥接 `app/grpc/generated/config/__init__.py` 自动解析，无需拷贝）
- `backend/modules/grpc/config_client.py`
  - 新增 `VideoMonitoringClient.notify_video_monitoring_changed(robot_id, enabled)`，走 `_dispatch_with_target(target="middleware", ...)`
  - 模块顶部地址解析规则注释补 `video.notify_video_monitoring → middleware`
- `backend/modules/robot/schemas/robot_config.py`：新增 `RobotVideoMonitoringControl { enabled: bool }`（robot_id 走 path）
- `backend/modules/robot/endpoints/robot_config.py`：新增 `POST /robot/config/video-monitoring/{robot_id}`，直接调 client、按 `resp.success` 返回 success/fail，**不走 service 层、不入重试**；复用权限 `robot:config:edit`

### 前端

- `frontend/src/service/api/robot.ts`：`fetchSetVideoMonitoring(robotId, enabled)` → `POST /robot/config/video-monitoring/{robotId}`，body `{ enabled }`
- `frontend/src/typings/api/robot.d.ts`：`Api.Robot.VideoMonitoringControl { enabled: boolean }`

## 约束与备注

- **明确不做**：不改 `retry_service._ROUTING`、不落库、不写 model/migration；不在 `app/grpc/generated/config/` 拷贝 pb2；不实现视频流渲染（`video-player.vue` 维持现状）。
- `backend/grpc` 是 git submodule，proto 与 generated 文件在其仓库内；本次仅本地生成未提交 submodule（按需由 owner 提交子模块并更新主仓库指针）。
- gRPC 生成脚本在 Windows GBK 控制台打印 emoji 会崩，需 `PYTHONUTF8=1 uv run python main.py`。
- 前端仅 `pnpm typecheck`（用户偏好不做界面测试）；现存 2 个 locale typecheck 报错（`map-editor` route key）为历史遗留，与本次无关。

## 相关文件

后端：
- `backend/grpc/protos/config/video.proto`
- `backend/grpc/generated/config/video_pb2.py`、`video_pb2_grpc.py`（生成）
- `backend/modules/grpc/config_client.py`
- `backend/modules/robot/schemas/robot_config.py`
- `backend/modules/robot/endpoints/robot_config.py`

前端：
- `frontend/src/service/api/robot.ts`
- `frontend/src/typings/api/robot.d.ts`

## 关联记忆

- 复用调度内核与地址解析：[[2026-06-24_param-config-grpc-scaffold]]、[[2026-06-25_param-config-grpc-from-robot]]
- 有意不接入重试队列：[[2026-06-25_grpc-push-retry-queue]]
- 同属 robot 参数配置端点族：[[2026-06-23_settings-and-task-multi-action-execution-record]]

## 记录日期

2026-07-06
