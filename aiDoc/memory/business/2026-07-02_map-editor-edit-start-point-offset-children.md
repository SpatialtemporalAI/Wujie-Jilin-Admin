# 地图编辑：编辑扫图起始点时按差值平移子元素

## 需求描述

编辑场景地图的「扫图起始点」(`start_point_x` / `start_point_y`，单位米) 后，将该场景地图下的子元素（标注/障碍物等）按「新旧值差值」平移。机器人坐标为独立世界坐标系（外部写入 DB），不需要变更。

触发时机：**后端 `SceneMapService.update`**，同一事务内完成，前端无需改动。

## 状态

已完成

## 设计要点（坐标换算）

子元素（标注 `x,y`、物体 `x,y`、路径中间点 `points`）按 start_point 新旧差值**直接相加**平移，**不涉及 resolution、不涉及 height**：

```
new_pixelX = old_pixelX + new_start_x - old_start_x
new_pixelY = old_pixelY + new_start_y - old_start_y
```

X、Y 均加上「新 − 旧」差值（同号）。数值用例：start_x 0→2 时 x 加 2；start_y 0→3 时 y 加 3；二者均变时 (10,20)→(12,23)。

> 注：公式经用户两次纠正定型。早期版本曾含 resolution 通式（保持世界坐标米），后改为「X 用 old−new、Y 含 height 翻转」，最终定型为上述「X/Y 均加 new−old、无 height」版本。

## 涉及范围

### 后端

- `backend/modules/scene/services/scene_map_service.py`：
  - `SceneMapService.update` 返回值由 `(map_obj, image_id_changed)` 扩展为 `(map_obj, image_id_changed, start_point_changed)`；更新前记录 `old_start_x/y`，更新后若 `start_point` 变化则调用 `_apply_start_point_offset` 并 `flush`。
  - 新增 `SceneMapService._apply_start_point_offset(...)`（参数：`map_id/old_start_x/old_start_y/new_start_x/new_start_y`，**无 resolution、无 height**）：
    - 标注：SQL `update()` 批量改 `x,y`（`map_id` + `deleted_at IS NULL`）。
    - 物体：SQL `update()` 批量改 `x,y`；**`points` 为相对物体自身原点的偏移**（nav_image 服务 `[(x+px, y+py)]` 印证），随 `x,y` 平移即可，不单独处理。
    - 路径：逐条 `json.loads(points)`，按绝对坐标平移每个 `{x,y}` 或 `[x,y]` 点后写回；起止为标注引用，随标注自动跟随。
- `backend/modules/scene/endpoints/scene_map.py` `update_map`：解包三元组返回值；`image_id_changed or start_point_changed` 均触发 `SceneMapNavImageService.schedule_regenerate`（start_point 变化会平移障碍物，nav_image 需重建）。
- 新增依赖导入：`json`、`sqlalchemy.update as sql_update`、`SceneMapAnnotation/SceneMapObject/SceneMapPath`。

### 前端

无改动。新增/编辑场景都走同一 `PUT /scene/map/{map_id}` → `update_map`，行为统一。

## 约束与备注

- 触发条件：`update_data` 含 `start_point_x` 或 `start_point_y`，且新值 ≠ 旧值。仅改名称等不触发。
- 不触碰机器人位置：机器人在独立世界系、由外部写入。
- 平移公式不含 resolution：按 start_point 新旧差值直接加减。
- 物体多边形 `points` 是相对偏移：仅平移 `x,y`，不动 `points`，避免双重平移。
- 路径中间点 `points` 当前编辑器不渲染（路径画为起止直线），但按绝对坐标平移以保数据一致；为空则跳过。
- nav_image 重建：start_point 变化已纳入 `schedule_regenerate` 触发条件。

## 相关文件

- `backend/modules/scene/services/scene_map_service.py`
- `backend/modules/scene/endpoints/scene_map.py`
- `frontend/src/utils/coordinate.ts`（换算公式来源，未改）

## 记录日期

2026-07-02
