# 任务管理：任务类型播报→巡逻时清空地图与机器人选择

## 需求描述

任务管理新增/编辑任务抽屉，任务类型从「播报」切换到「巡逻」时，需清空已选的场景地图与机器人（及派生的巡逻点位/点位选项），避免播报阶段的选择残留到巡逻场景。

## 关键实现

- `frontend/src/views/task/modules/task-operate-drawer.vue`：
  - 新增 `handleTaskTypeChange(val)`：记录 `previous = model.task_type` 后赋新值；仅 `previous==='broadcast' && val==='patrol'` 时清空 `map_id=null`、`robot_ids=[]`、`points=[]`、`annotationOptions=[]`、`annotationMap=new Map()`、`mapOptions=[]`、`mapOptionsLoaded=false`（与 handleMapChange 清空范围一致 + 重置地图下拉加载态）。
  - 「任务类型」`NRadioGroup` 由 `v-model:value` 改为 `:value` + `@update:value="handleTaskTypeChange"`，以便在赋新值前拿到旧类型判断方向。

## 约束与备注

- 只处理「播报→巡逻」单向：巡逻需先选场景地图再按场景约束选机器人，播报选的机器人/地图不适用；反向「巡逻→播报」不清空——播报不绑地图（提交时 map_id 强制 null）、单机器人可沿用，符合既有提交逻辑（见 `handleSubmit` 的 `map_id: isPatrol ? ... : null`）。
- `pnpm typecheck` 通过；未做界面测试（遵循 [[feedback-typecheck-only]]）。

## 相关文件

- 前端：`frontend/src/views/task/modules/task-operate-drawer.vue`

## 记录日期

2026-07-15
