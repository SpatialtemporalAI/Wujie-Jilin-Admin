---
name: robot-event-log-status-rename
description: 机器人事件日志 event_status 枚举值重命名：normal→info、abnormal→critical、warning 不变；全栈字面值替换，不迁移存量、不兼容旧值，外部写入源同步改
metadata:
  type: business
---

# 2026-07-20 机器人事件日志 event_status 枚举值重命名

## 需求

`robot_event_log.event_status` 的取值由 `normal / abnormal / warning` 改为 `info / warning / critical`：

- `normal` → `info`（正常恢复）
- `abnormal` → `critical`（严重故障）
- `warning` → `warning`（告警提示，不变）

纯字面值重命名，不改类型（仍是 `String(20)`）。

## 决策

- **不处理存量数据**：库里已有的 `normal/abnormal` 旧值不迁移；改后旧值在前端表格回退显示为原始字符串，后端查询参数校验（`parse_optional_enum`）会拒绝旧值。
- **不兼容旧值**：后端读取/响应不做新旧映射。
- **外部写入源同步改**：向 `robot_event_log` 写入 `event_status` 的外部系统（gRPC/MQTT，不在本仓库）会同步改用新值，本仓库只需保证自身前后端一致。
- **不改历史迁移**：`0010_robot_event_log.py` 的建表注释保留旧字面值（历史快照，已执行，不动）。

## 关键实现

后端：

- `modules/robot/schemas/robot_event_log.py`：`EventStatusField` 枚举 `{normal,abnormal,warning}` → `{info,warning,critical}`，Field description 同步。
- `database/models/business/robot_event_log.py`：`event_status` 列注释改为 `info-正常，warning-告警，critical-严重`。
- `modules/admin/exports/robot_event_log_export.py`：`EVENT_STATUS_MAP` 的 key 由 `abnormal/warning/normal` 改为 `critical/warning/info`（中文文案值不变）。

前端：

- `views/log/robot-log/modules/robot-event-log-search.vue`：`eventStatusOptions` 三项 value 改 `critical/warning/info`。
- `views/log/robot-log/index.vue`：表格列 `statusMap` 的 key 改 `critical/warning/info`。
- `views/operation-monitor/modules/alert-panel.vue`：`mapAlertSeverity` 与 `getEventStatusLabel` 的判断值改 `critical/warning/info`。
- i18n key 本就叫 `statusCritical/statusWarning/statusInfo`，与新值同名，中英文案无需改动。

## 涉及文件

- 后端：`backend/modules/robot/schemas/robot_event_log.py`、`backend/database/models/business/robot_event_log.py`、`backend/modules/admin/exports/robot_event_log_export.py`
- 前端：`frontend/src/views/log/robot-log/modules/robot-event-log-search.vue`、`frontend/src/views/log/robot-log/index.vue`、`frontend/src/views/operation-monitor/modules/alert-panel.vue`
- 边界文档：`aiDoc/frontend-backend/boundary.md`

## 约束与备注

- 后端无 `event_status` 写入逻辑，数据由外部系统推送；外部系统需同步改用新值，否则新旧值混用、旧值会被查询枚举校验拒绝。
- 历史记忆 [[robot-event-log-status-labels]] / [[robot-event-log-search-export-fix]] / [[operation-monitor-alert-event-status-prefix]] 记录的是改名前的事实，保留作快照。
- 承接 [[robot-event-log-search-export-fix]]：那次把后端枚举对齐到 `{normal,abnormal,warning}`，本次在此基础上整体重命名。

## 记录日期

2026-07-20
