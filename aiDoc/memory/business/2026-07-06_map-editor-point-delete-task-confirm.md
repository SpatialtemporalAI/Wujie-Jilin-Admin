# 地图编辑：删除点位仅在其已关联任务时弹窗确认

## 需求描述

地图编辑器删除点位（annotation）时，**仅当该点位已被任务（`task_point.annotation_id`）引用**时才弹出二次确认弹窗；未关联任务的点位直接删除，不再弹窗。

此前行为：选中任意点位按 `Delete`/右键删除/属性面板删除，都会弹出"当前点位已有关联任务…"的确认框，即使该点位并无任务关联——文案具有误导性。

## 状态

已完成

## 设计要点

**判定数据来源：编辑器数据加载时一次性回填 `task_count`。**

- 编辑器本身不创建任务，单次编辑会话内点位与任务的关联关系稳定；后端保存时 `SceneMapEditorService.save_editor_data` → `TaskService.delete_points_by_annotation_ids` 仍按实时 DB 状态清理任务点位，因此即便前端 `task_count` 过期也不会产生脏数据。
- 新建未保存的点位（前端临时负 id）天然无任务关联 → `task_count` 缺省为 0 → 直接删除。

## 涉及范围

### 后端

- `backend/modules/task/services/task_service.py`：
  - 新增 `TaskService.count_tasks_by_annotation_ids(db, annotation_ids) -> dict[int, int]`：`JOIN Task` 后按 `TaskPoint.annotation_id` 分组、`COUNT(DISTINCT task_id)`，仅统计 `Task.deleted_at IS NULL AND TaskPoint.deleted_at IS NULL` 的有效关联；空入参直接返回 `{}`。
  - 新增 `from sqlalchemy import func`。
- `backend/modules/scene/schemas/scene_map_editor.py`：
  - `EditorMapAnnotationResponse` 新增 `task_count: int = Field(0, ...)`（`from_attributes=True` 下 ORM 无此字段，缺省 0，由端点手动赋值）。
- `backend/modules/scene/endpoints/scene_map_editor.py`：
  - `get_editor_data` 收集 `map_obj.annotations` 的 id，调用 `count_tasks_by_annotation_ids` 得到映射，逐个 `model_validate(a)` 后写 `resp.task_count = task_counts.get(a.id, 0)`。
  - 新增 `from modules.task.services.task_service import TaskService`。

### 前端

- `frontend/src/typings/api/scene.d.ts`：`SceneMapAnnotation` 新增 `task_count?: number`（仅编辑器数据接口回填；其它接口不返回，按 undefined 处理）。
- `frontend/src/views/scene/map-editor/index.vue`：
  - `confirmAndRemoveElement(target)`：若 `target.type === 'annotation'`，查 `task_count`；`<= 0` 直接 `editor.removeElement(...)`，`> 0` 才 `dialog.warning` 弹窗并把文案改为"当前点位已关联 {N} 个任务…"。非点位（障碍物/禁区/电子围栏）保持原有通用确认。
  - 新增 `handleRemoveElement(type, id)`：annotation 走 `confirmAndRemoveElement`，其余直接 `editor.removeElement`。模板 `PropertyPanel` 的 `@remove-element` 由 `editor.removeElement` 改绑到 `handleRemoveElement`。
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`：
  - 点位列表项的删除按钮去掉常驻 `NPopconfirm`（其文案"当前点位已有关联任务…"对无任务点位具有误导性），改为直接 `emit('remove-element', 'annotation', ann.id)`，由父级 `handleRemoveElement` 统一按 `task_count` 决定是否确认。
  - "删除此点位"按钮（编辑区）与"删除此物体"按钮不变，仍直接 emit，由父级分流。

## 约束与备注

- 删除路径统一：键盘 `Delete`/`Backspace`、右键菜单删除、属性面板点位列表项、属性面板"删除此点位"按钮——点位均经 `confirmAndRemoveElement`，由 `task_count` 决定弹窗与否。
- 障碍物/禁行区域/电子围栏删除仍保持通用确认弹窗（与本次需求无关）。
- `task_count` 为加载时快照：跨页面在编辑器打开期间新建引用该点位的任务不会反映到前端；但保存时后端按实时 DB 清理任务点位，无数据完整性风险。

## 相关文件

- `backend/modules/task/services/task_service.py`
- `backend/modules/scene/schemas/scene_map_editor.py`
- `backend/modules/scene/endpoints/scene_map_editor.py`
- `frontend/src/typings/api/scene.d.ts`
- `frontend/src/views/scene/map-editor/index.vue`
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`

## 记录日期

2026-07-06
