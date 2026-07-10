---
name: operation-monitor-livekit-video
description: 运行监控页实时视频接入 LiveKit，后端 Redis 维护观众计数实现单机器人多用户共享摄像头
metadata:
  type: business
---

# 2026-07-10 运行监控实时视频接入 LiveKit

## 需求

在运行监控页（`/operation-monitor`）的「视频监控」Tab 中，通过 LiveKit 实时显示机器人摄像头画面；页面关闭时关闭摄像头；同一机器人被多个用户同时观看时，物理摄像头只在最后一个观众离开时才关闭。

## 关键设计

- **后端**：复用 `POST /admin/robot/config/video-monitoring/{robot_id}`，扩展为打开时返回 LiveKit Token/房间名/观众 ID，关闭时携带观众 ID；Redis SET + TTL 维护观众计数，首个观众触发 gRPC 开启摄像头，最后一个观众离开触发 gRPC 关闭。
- **房间名**：机器人 `serial_number`。
- **权限**：使用已有 `robot:monitor:list`。
- **心跳**：前端每 15s 调用 `/heartbeat`，租约 60s；30s 清理任务兜底处理浏览器崩溃。
- **前端**：新增 `useLiveKitVideo` composable，`video-player.vue` 接入 `livekit-client`。

## 涉及文件

- 后端：
  - `backend/core/config/settings_model.py`
  - `backend/core/config/settings.py`
  - `backend/.env.dev`
  - `backend/pyproject.toml`
  - `backend/modules/robot/schemas/robot_config.py`
  - `backend/modules/robot/services/livekit_video_service.py`
  - `backend/modules/robot/endpoints/robot_config.py`
  - `backend/modules/scheduler/tasks/robot_video.py`
  - `backend/main.py`
- 前端：
  - `frontend/src/typings/api/robot.d.ts`
  - `frontend/src/service/api/robot.ts`
  - `frontend/src/views/operation-monitor/composables/useLiveKitVideo.ts`
  - `frontend/src/views/operation-monitor/modules/video-player.vue`
  - `frontend/src/views/operation-monitor/index.vue`

## 业务规则

1. 只有机器人 `status == online` 时才允许打开视频。
2. 多个用户打开同一机器人视频时，仅第一次真正下发 gRPC 开启摄像头。
3. 用户关闭/离开（组件 unmount）时递减计数；计数到 0 才下发 gRPC 关闭摄像头。
4. 浏览器崩溃等异常断连通过 Redis TTL + 定时清理任务兜底关闭摄像头。
5. Token 为 subscriber-only（`canSubscribe=true, canPublish=false, canPublishData=false`）。

## 环境配置

启用前需在 `.env.dev` 配置：

```env
LIVEKIT__ENABLED=true
LIVEKIT__API_KEY=...
LIVEKIT__API_SECRET=...
LIVEKIT__WS_URL=wss://...
```

## 后续注意

- 机器人 middleware 需自行配置 LiveKit 发布者凭据，并以机器人 `serial_number` 作为房间名加入房间。
- 如需按钮级细粒度权限，可新增 `robot:monitor:video`。
