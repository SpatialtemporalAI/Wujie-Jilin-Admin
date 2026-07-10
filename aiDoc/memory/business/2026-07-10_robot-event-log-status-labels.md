---
name: robot-event-log-status-labels
description: 机器人事件日志去掉事件类型显示，事件状态调整为严重故障/告警提示/正常恢复三色标签；实时告警仅展示选中机器人最新 10 条
metadata:
  type: business
---

# 2026-07-10 机器人事件日志与实时告警样式调整

## 需求

1. 机器人事件日志页面：
   - 去掉「事件类型」列和搜索条件；
   - 事件状态标签改为三种：
     - 严重故障｜Critical — 红色（`error`）
     - 告警提示｜Warning — 黄色（`warning`）
     - 正常恢复｜Info — 蓝色（`info`）
2. 运行监控页实时告警卡片：
   - 使用与事件日志相同的三色规则；
   - 仅展示当前选中机器人的最新 10 条数据。

## 关键实现

- 后端事件状态仍为 `normal` / `abnormal`，前端映射为：
  - `abnormal` → 严重故障 / Critical / 红色
  - `warning` → 告警提示 / Warning / 黄色（预留）
  - `normal` → 正常恢复 / Info / 蓝色
- 事件日志表格移除 `event_type` 列，搜索表单移除事件类型下拉。
- 实时告警 `page_size` 由 20 调整为 10。

## 涉及文件

- `frontend/src/views/log/robot-log/index.vue`
- `frontend/src/views/log/robot-log/modules/robot-event-log-search.vue`
- `frontend/src/views/operation-monitor/modules/alert-panel.vue`
- `frontend/src/locales/langs/zh-cn.ts`
- `frontend/src/locales/langs/en-us.ts`
- `frontend/src/typings/app.d.ts`

## 维护说明

- i18n 键已同步更新：`statusCritical`、`statusWarning`、`statusInfo`。
- 若后端后续扩展 `warning` 状态，前端映射已预留，无需再改。
