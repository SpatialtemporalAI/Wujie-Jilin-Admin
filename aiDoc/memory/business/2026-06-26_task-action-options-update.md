# 任务运控动作选项更新 & 允许点位动作为空

## 需求描述

任务管理「任务列表」新增/编辑任务时：

1. **允许点位的运控动作列表整体为空**：此前 `TaskPointCreate.actions` 在后端 `min_length=1`，前端有「至少添加一个运控动作」+「每个动作必须选择运控类型」双重校验，新增点位时硬塞一个 `wave` 默认项。改为允许点位不带任何动作项（动作列表可为空）。
2. **下拉选项替换为真实机器人支持的运控动作**：
   - `shake_hands`（握手）
   - `wave`（挥手）
   - `left_hand`（伸左手）
   - `right_hand`（伸右手）
   - `bend_no_hands`（弯腰）
   - `bend_with_hands`（弯腰和伸手）
   - `no`（无动作）—— 新增的显式「无动作」选项

原 `bow / turn / wait / nod` 等占位值从下拉中移除，但详情抽屉保留对应中文标签兼容历史快照数据。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/task/schemas/task.py`
  - `TaskActionItem.action`（L37）：仍保留必填，仅更新 `description` 列出新合法值
  - `TaskPointCreate.actions`（L46）：去掉 `min_length=1`，改为 `Field(default_factory=list)`，允许空列表
  - `TaskPointResponse.actions`（L58）：同样改为 `default_factory=list`，避免响应字段必填
- `backend/modules/task/services/task_execution_record_service.py`
  - L57 快照回填默认值 `a.get("action", "wave")` → `a.get("action", "no")`

> `TaskActionSnapshot.action`（`schemas/task_execution_record.py:27`）保持 `Field(...)` 必填——快照里只要写了动作项就必须有 `action` 值，与「列表可为空、单项必填」语义一致。

### 前端

- `frontend/src/typings/api/task.d.ts`
  - `TaskAction`（L15）替换为新七项枚举
- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - `actionOptions`（L35-42）：替换为新七项
  - `addPoint`（L200）/`addAction`（L213）：默认 action `'wave'` → `'no'`
  - `handleInitModel`（L270-274 / L290-294）：编辑回填时点位 `actions` 为空则保留空数组，不再塞默认项；历史 action 值缺失时 fallback 到 `'no'`
  - 提交校验：删除「请为点位 X 至少添加一个运控动作」整段；保留「请选择点位 X 中动作 Y 的运控类型」单项必填校验
  - `<NFormItemGi label="动作" required>` 与 `<NSelect>`：保留 `required`、不开 `clearable`，避免出现「动作项存在但 action 为空」的脏数据
- `frontend/src/views/task/modules/task-detail-drawer.vue`
  - `actionLabel`（L38-44）：替换为新七项标签，保留 `bow/turn/wait/nod` 老值标签以兼容历史快照显示

## 约束与备注

- **单项 action 仍然必填**：列表可为空，但只要添加了动作项，就必须选定一个 action 值。`TaskActionItem.action` 后端 `Field(...)`、前端 `<NFormItemGi required>` + 单项校验保留。
- **新增动作项默认值**：`'no'`（无动作），与「允许列表为空」的语义对齐；用户可主动改为其他具体动作。
- **DB 无需迁移**：`TaskPoint.actions` 本就是 `JSON nullable=True`，新枚举值直接以字符串透传到 gRPC 推送与执行快照，无需改 proto 或客户端。
- **历史数据兼容**：详情抽屉的 `actionLabel` 保留 `bow/turn/wait/nod` 中文标签；编辑抽屉里若老任务的 action 值不在新选项中，NSelect 会显示为空，用户需重新选择新值保存。

## 相关文件

- `backend/modules/task/schemas/task.py`
- `backend/modules/task/services/task_execution_record_service.py`
- `frontend/src/typings/api/task.d.ts`
- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `frontend/src/views/task/modules/task-detail-drawer.vue`

## 记录日期

2026-06-26
