---
name: operation-monitor-alert-event-status-prefix
description: 运行监控实时告警卡片在每条事件标题前增加事件状态标签（严重故障/告警提示/正常恢复），与机器人事件日志 statusMap 文案一致
metadata:
  type: business
---

# 2026-07-17 实时告警事件状态前置显示

## 需求

运行监控页「实时告警」卡片，原来只用 `event_status` 推导严重度颜色/图标，但不显示状态文案。要求在每条事件标题前面显示事件状态。

## 关键实现

- `AlertItem` 新增 `statusLabel` 字段。
- 新增 `getEventStatusLabel(event_status)`，文案与 `robot-log/index.vue` 的 `statusMap` 保持一致：
  - `abnormal` → 严重故障
  - `warning` → 告警提示
  - `normal` → 正常恢复
  - 其它 → 原始 `event_status` 值，缺省回退「告警」
- 模板结构（图标右侧内容区自上而下）：`NTag` 状态标签 → 事件标题 → 时间。标签独占一行，标题不缩略（`break-all` 完整换行）。`NTag` 的 `type` 取 `alert.severity`，`size="small"` `:bordered="false"`。
- `severity` 仍由 `mapAlertSeverity` 推导，同时驱动颜色与标签 type，颜色与标签保持一致。

## 涉及文件

- `frontend/src/views/operation-monitor/modules/alert-panel.vue`

## 约束与备注

- 告警面板沿用硬编码中文（文件原有风格，未引入 `$t`）；如后续整体接入 i18n，应改用 `page.log.robotEventLog.statusCritical/statusWarning/statusInfo`。
- 与 [[robot-event-log-status-labels]] 衔接：那次确定了三色规则与本卡片的 10 条上限，本次只是补上状态文案的前置展示。
