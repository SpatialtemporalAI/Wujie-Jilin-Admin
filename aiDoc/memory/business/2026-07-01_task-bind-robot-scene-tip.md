# 任务绑定机器人与场景一致性提示

## 需求描述

任务管理-新增/编辑任务抽屉中，在「任务类型」选择项下方新增一条醒目提示词：「注意：任务绑定机器人后，若机器人不在任务绑定的场景下，该任务无法执行！」，用于提醒用户机器人所在场景需与任务绑定场景一致，否则任务无法执行。

## 状态

已完成

## 涉及范围

### 后端

无。仅前端纯展示文案调整，不涉及接口与数据契约。

### 前端

- `task-operate-drawer.vue` 基础信息 `NGrid` 内，「任务类型」`NFormItemGi` 之后新增一个 `NGi :span="2"`，包裹一条 `NAlert type="warning"` 展示提示文案。
- 使用 `NAlert`（warning）而非普通文字，更醒目；`NGi :span="2"` 占满整行，与任务类型对齐。
- 组件均经 `components.d.ts` 自动注册，无需手动 import。

## 约束与备注

- 仅作用于 `frontend/src/views/task/modules/task-operate-drawer.vue`（巡逻/播报任务管理抽屉）。
- 同名文件 `frontend/src/views/manage/scheduler/modules/task-operate-drawer.vue` 为 cron 调度框架任务，无「任务类型/机器人/场景」概念，不在本次范围内。
- 与既有「场景地图→绑定机器人」联动逻辑（机器人需在所选场景内）一致，本提示为前置预警，不改变校验行为。

## 相关文件

- frontend/src/views/task/modules/task-operate-drawer.vue

## 记录日期

2026-07-01
