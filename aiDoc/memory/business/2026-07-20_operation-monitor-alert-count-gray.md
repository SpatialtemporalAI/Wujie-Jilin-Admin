---
name: operation-monitor-alert-count-gray
description: 运行监控实时告警卡片标题旁的告警数量 NTag 由红色(error)改为灰色(default)，弱化数量视觉权重
metadata:
  type: business
---

# 2026-07-20 实时告警数量标签改灰色

## 需求

运行监控页「实时告警」卡片标题旁的告警数量 `NTag`，由 `type="error"`（红色）改为 `type="default"`（灰色），弱化数量本身的视觉权重。

## 关键实现

- `frontend/src/views/operation-monitor/modules/alert-panel.vue`：标题区数量 `NTag` 的 `type` 由 `error` 改 `default`，`size="small" round` 不变。

## 涉及文件

- `frontend/src/views/operation-monitor/modules/alert-panel.vue`

## 约束与备注

- 仅改标题旁的数量标签颜色；下方告警列表项的严重度颜色（error/warning/info）与 [[operation-monitor-alert-event-status-prefix]] 的状态前置标签不动。
- 与同日 [[robot-event-log-status-rename]] 无直接关联，纯属同一会话的样式微调。

## 记录日期

2026-07-20
