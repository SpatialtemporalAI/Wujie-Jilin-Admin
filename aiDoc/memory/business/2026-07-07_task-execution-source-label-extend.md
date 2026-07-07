# 执行详情触发源补充「语音输入」「手动恢复」

## 需求描述

任务执行详情抽屉的「触发源」展示补充两项：`text_input` → 语音输入、`resume` → 手动恢复。此前 `sourceLabelMap` 只覆盖 platform_schedule / voice_trigger / manual，agent 侧写入的 text_input / resume 会显示原始英文 key。

## 状态

已完成

## 涉及范围

### 后端

无改动。

### 前端

- `frontend/src/views/task/modules/task-detail-drawer.vue`：`sourceLabelMap` 追加 `text_input: '语音输入'`、`resume: '手动恢复'`。第 117 行 `sourceLabelMap[detail.source] || detail.source` 查表逻辑本就支持，未知回退原值。

## 约束与备注

- **只改详情抽屉展示**：执行列表 / 历史列表表格目前没有「触发源」列（columns 只有 task_name/task_type/status/robot_name/scene_name/time/operate），历史搜索下拉也没有 source 筛选，本次按用户确认**不新增列、不加筛选**。
- **数据来源**：本后端无任何创建 `TaskExecutionRecord` 的代码（`start_execution` 仅下发 gRPC run_now，注释明确"执行记录由 agent 侧维护，平台不再落库"）。`source` 值由 agent 端写入数据库，不经过本后端 schema 的 `Literal["platform_schedule","voice_trigger","manual"]` 校验，故前端补充展示即可生效。
- **后端枚举未扩展**：`ExecutionSourceField`（查询）与创建 schema 的 `Literal` 仍是三个原值。因当前无 source 搜索 UI，不影响使用；若后续历史列表要加触发源筛选，需同步把 text_input/resume 加进 `ExecutionSourceField` 与 `parse_optional_enum` 集合。
- `resume_execution` 只改 status、不写 source 字段；此处的 `resume` source 是 agent 侧对「手动恢复触发」的语义标记，与平台 `resume_execution` 方法无直接关系。

## 相关文件

- `frontend/src/views/task/modules/task-detail-drawer.vue`

## 记录日期

2026-07-07
