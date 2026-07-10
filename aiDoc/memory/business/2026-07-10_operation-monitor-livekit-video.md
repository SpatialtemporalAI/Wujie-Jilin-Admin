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

## 问题排查：Token 返回但无法打开视频

> 用户反馈：`POST /admin/robot/config/video-monitoring/{robot_id}` 已返回 token，但前端无法正确打开视频。

### 已修复/已增强

1. **前端错误处理**：`useLiveKitVideo.ts` 打开票据时增加 `error` 判断，避免请求失败时仍尝试连接；并补充 `ConnectionStateChanged / Disconnected` 日志。
   - 文件：`frontend/src/views/operation-monitor/composables/useLiveKitVideo.ts`
2. **前端视频元素保持挂载**：`video-player.vue` 改为始终渲染 `<video>`（通过 `opacity-0` 隐藏），避免连接过程中 `videoRef` 被 `v-if` 卸载，导致 LiveKit 轨道订阅成功却无法 `attach` 到 DOM。
   - 文件：`frontend/src/views/operation-monitor/modules/video-player.vue`
3. **后端房间名校验**：生成 Token 前校验 `serial_number` 是否符合 LiveKit 房间名规则（字母、数字、下划线、连字符，长度 1-64），不符合直接返回明确错误。
   - 文件：`backend/modules/robot/services/livekit_video_service.py`
4. **后端生成日志**：Token 生成时记录 `serial_number / user_id / viewer_id / ttl / api_key 前缀`，便于排查。

### 仍需确认

若上述修复后仍无法打开，请提供以下信息进一步定位：

1. 浏览器控制台 `LiveKit 连接失败 / LiveKit 已断开连接 / LiveKit 连接状态变化` 的完整日志。
2. 后端日志中本次调用的 `生成 LiveKit Token` 行。
3. 机器人 `serial_number` 的具体值。
4. LiveKit 服务端是否已运行、是否可达、`LIVEKIT__WS_URL` 配置是否与服务端一致。
5. 机器人 middleware 是否已按 `serial_number` 作为房间名加入房间并发布视频轨道。

### 常见根因

- **房间名不合法**：`serial_number` 含 `.`、`:`、空格、中文等字符会导致 LiveKit 拒连。
- **middleware 未进房推流**：Token 有效但房间内无视频轨道，前端会连接成功却黑屏。
- **网络 / CORS / 协议不匹配**：前端无法访问 `LIVEKIT__WS_URL`，或 `ws://` 与 `https` 页面混用被浏览器拦截。
- **API Key/Secret 不匹配**：服务端校验 Token 失败。

状态：**前端视频挂载 + 错误处理 + 后端校验已修复；等待用户反馈控制台/后端日志**
