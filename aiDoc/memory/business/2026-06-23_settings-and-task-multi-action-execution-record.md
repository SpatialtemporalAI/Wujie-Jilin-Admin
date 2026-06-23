# 参数配置权限/滚动 + 任务点位多动作 + 独立执行记录表

**日期**: 2026-06-23
**提出者**: 用户

## 需求概述

5 个关联改造需求，覆盖参数配置（settings）页面权限/布局优化，以及任务管理模块的多动作点位和新执行记录表。

## 用例清单

| 编号 | 名称 | 说明 |
|------|------|------|
| UC-A | settings 页面权限修复 | 4 个 tab 的所有写入按钮统一加 `robot:config:edit` 权限控制 |
| UC-B | settings 页面滚动 | 主页面根容器加 `overflow-y-auto`，内容超出时可纵向滚动 |
| UC-C | 人脸识别表单折叠 | 保存配置按钮同行最右侧加展开/收起按钮，控制表单显示 |
| UC-D | 任务点位多动作 | 一个点位支持配置多个动作（JSON 方案） |
| UC-E | 独立执行记录表 | 新建 `task_execution_record` 表存储任务定义快照与详细进度 |

## 关键业务规则

### UC-A: settings 权限统一
- 所有写入操作（保存/测试/上传/编辑/删除）统一使用 `robot:config:edit`
- 后端权限定义已存在，无需新增
- 涉及文件：4 个 tab 文件 + voice/face/speed/battery 模块

### UC-B: settings 滚动
- 使用 `<div class="h-full overflow-y-auto">` 包裹 NCard
- 参照 [operation-monitor/index.vue](frontend/src/views/operation-monitor/index.vue) 模式

### UC-C: 表单展开/收起
- 使用 `v-show` 控制表单显示
- 图标使用 `mdi:chevron-up/down`
- 展开/收起按钮与保存按钮同行（`flex justify-between`）

### UC-D: 点位多动作
- 数据库：`task_point.action` + `task_point.voice_text` 合并为 `actions` JSON
- 格式：`[{"action":"wave","voice_text":"欢迎"},...]`
- 至少一个动作（前端校验）
- 迁移文件 `0024_task_point_actions_json.py`

### UC-E: 独立执行记录表
- 新表 `task_execution_record`，与旧 `task_execution` 表并存（旧表停止写入）
- 字段：`id/robot_id/scene_id/user_id/task_definition(JSON)/progress(JSON)/progress_per/status/source/error_msg/start_time/finish_time`
- status: `pending/running/paused/completed/cancelled/failed`
- source: `platform_schedule/voice_trigger/manual`
- 启动任务时构建 task_definition 快照（task+points+actions），写入新表
- 一个任务在多个机器人上同时执行时，每个机器人创建一条独立记录
- 迁移文件 `0025_task_execution_record_table.py`

## 实现范围

### 前端
- 修改 `frontend/src/views/settings/index.vue`（滚动）
- 修改 `frontend/src/views/settings/modules/{voice-synthesis,face-recognition,walking-speed,battery-threshold}-tab.vue`（权限+展开收起）
- 修改 `frontend/src/views/task/modules/task-operate-drawer.vue`（多动作表单）
- 修改 `frontend/src/views/task/modules/task-list-tab.vue`（启动用新 API）
- 修改 `frontend/src/views/task/modules/task-execution-tab.vue`（用新 API/字段）
- 修改 `frontend/src/views/task/modules/task-history-tab.vue`（用新 API/字段）
- 修改 `frontend/src/views/task/modules/task-detail-drawer.vue`（用新详情 API）
- 修改 `frontend/src/views/task/modules/task-history-search.vue`（字段改为 scene_id）
- 修改 `frontend/src/typings/api/task.d.ts`（新增多动作 + 执行记录类型）
- 修改 `frontend/src/service/api/task.ts`（新增 7 个 execution-record API）

### 后端
- 修改 `backend/database/models/business/task_point.py`（actions JSON）
- 修改 `backend/database/models/business/__init__.py`（导入 TaskExecutionRecord）
- 新增 `backend/database/models/business/task_execution_record.py`
- 修改 `backend/modules/task/schemas/task.py`（TaskActionItem/TaskPointCreate）
- 新增 `backend/modules/task/schemas/task_execution_record.py`
- 修改 `backend/modules/task/services/task_service.py`（create/update 用 actions）
- 新增 `backend/modules/task/services/task_execution_record_service.py`
- 新增 `backend/modules/task/endpoints/task_execution_record.py`
- 修改 `backend/modules/task/router.py`（注册新路由）
- 新增 `backend/database/alembic/versions/0024_task_point_actions_json.py`
- 新增 `backend/database/alembic/versions/0025_task_execution_record_table.py`

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 多动作存储方式 | JSON 字段 | 改动小，单表完成，前端无需 JOIN |
| 新执行表处理方式 | 新建并废弃旧表 | 用户明确要求"创建一张单独的任务表" |
| task_definition 数据来源 | 启动时快照 | 隔离任务定义变更对历史执行记录的影响 |
| settings 权限粒度 | 统一 `robot:config:edit` | 与后端现有权限一致，无需新增 |
| 旧 task_execution 表 | 暂保留不删除 | 避免破坏性变更，后续单独清理 |
