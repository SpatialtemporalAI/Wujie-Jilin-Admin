---
name: operation-monitor-video-overlay-stats
description: 运行监控视频监控去掉底部「直播中」，视频居左，顶部叠加显示实时时间/分辨率/帧率/全屏
metadata:
  type: business
---

# 2026-07-16 视频监控叠加状态信息（时间/分辨率/帧率/全屏）

## 需求

运行监控页（`/operation-monitor`）「视频监控」Tab 的视频播放区调整为：

1. **去掉底部「直播中」文字**（原视频下方 `mt-8px text-success` 那一行删除）。
2. **视频居左显示**：视频画面在容器内左对齐，不再水平居中留黑边。
3. **新增叠加显示**：实时时间、分辨率、帧率、全屏按钮，集中在视频顶部一条半透明状态条上。

## 关键设计

- `useLiveKitVideo` 新增对外暴露 `resolution`（如 `1920×1080`）与 `frameRate`（如 `30`）两个 ref。
  - 数值来自已附加视频轨 `track.mediaStreamTrack.getSettings()` 的 `width/height/frameRate`。
  - attach 后启动 1s 轮询读取（`metricsTimer`），用于反映 LiveKit `adaptiveStream` 动态分辨率变化。
  - 断开/取消发布/组件卸载时 `resetMetrics()` 清理定时器与数值。
- `video-player.vue`：
  - 移除底部「直播中」`<div>`。
  - `<video>` 加 `style="object-position: left center"` 实现画面居左（容器仍 `absolute inset-0 object-contain`，仅调整对象定位）。
  - 顶部叠加 `bg-black/40` 状态条：左 `currentTime`（组件内 1s 定时器格式化 `HH:mm:ss`），右 `resolution` / `frameRate fps` / 全屏按钮。
  - 全屏由原右上角 `NButton` 改为状态条内的原生 `<button>`（白色图标，适配深色叠加层）。

## 涉及文件

- `frontend/src/views/operation-monitor/composables/useLiveKitVideo.ts`
- `frontend/src/views/operation-monitor/modules/video-player.vue`

## 业务规则

1. 叠加状态条仅在 `connected`（视频轨已附加）时显示。
2. 分辨率/帧率来自浏览器 `MediaStreamTrack.getSettings()`，对远端 WebRTC 轨同样有效；读不到时该项不渲染（`v-if`），不报错。
3. 全屏目标仍是视频外层 `containerRef`（与原实现一致），叠加状态条随容器一起全屏。

## 关联记忆

- [[operation-monitor-livekit-video]] — 运行监控页视频监控 LiveKit 接入与观众计数设计
- [[operation-monitor-video-switch-robot]] — 切换机器人时先关旧再开新

## 记录日期

2026-07-16
