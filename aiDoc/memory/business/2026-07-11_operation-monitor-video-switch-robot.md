---
name: operation-monitor-video-switch-robot
description: 运行监控页视频监控 Tab 切换机器人时，必须先关闭原机器人视频再打开新机器人视频
metadata:
  type: business
---

# 2026-07-11 视频监控 Tab 切换机器人时先关旧再开新

## 需求

在运行监控页（`/operation-monitor`）的「视频监控」Tab 中，用户通过顶部机器人下拉切换机器人时，必须保证：

1. **先关闭原机器人的视频流**（释放 LiveKit 连接、停止心跳、通知后端关闭旧观众会话）。
2. **再打开新机器人的视频流**（重新获取票据、连接 LiveKit、启动心跳）。

避免旧视频连接未正确释放即开始新连接，导致后台观众计数泄漏或摄像头无法按预期关闭。

## 关键设计

- `useLiveKitVideo` 内部维护当前会话的 `sessionRobotId` 与 `sessionViewerId`，专门用于 `disconnect()` 调用后端关闭接口。
- `connect()` 开始时会先 `await disconnect()`，确保旧会话使用旧 `sessionRobotId/sessionViewerId` 关闭，随后再用新机器人信息创建新会话。
- `video-player.vue` 直接传入 `props` 对象，使 `useLiveKitVideo` 内部 `watch` 能响应 `robotId / serialNumber / status` 的变化，切换机器人时自动触发 `connect()`。

## 涉及文件

- `frontend/src/views/operation-monitor/composables/useLiveKitVideo.ts`
- `frontend/src/views/operation-monitor/modules/video-player.vue`

## 业务规则

1. 切换机器人属于同一个 `video-player.vue` 组件实例内的状态变化，不通过 `:key` 强制重建组件。
2. 关闭旧视频必须携带**旧会话的 robot_id 与 viewer_id**，不能误用新机器人的 `robotId`。
3. 新机器人 `status !== online` 时只关闭旧视频，不再尝试打开新视频。

## 关联记忆

- [[operation-monitor-livekit-video]] — 运行监控页视频监控 LiveKit 接入与观众计数设计

## 记录日期

2026-07-11
