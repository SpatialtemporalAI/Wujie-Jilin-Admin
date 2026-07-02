# 地图编辑器新增场景：上传 ROS yaml 配置解析分辨率与起始点

## 需求描述

地图编辑器新增场景时，将「扫图起始点 X/Y」「分辨率」输入框改为 **disabled**，并在「场景图片」上传下方新增「配置文件」上传（yaml 类型）。上传 ROS 地图配置文件后，后端解析其中的 `resolution` 与 `origin`，前端回显：
- `resolution` → 分辨率（`sceneFormResolution`）
- `origin[0]` / `origin[1]` → 扫图起始点 X / Y（`sceneFormPointX` / `sceneFormPointY`）

**不改动原有 `scene/map/add` 新增接口**，新增独立的 yaml 解析接口处理。yaml 示例：

```yaml
image: map.png
resolution: 0.05
origin: [-3.2147998809814453, -15.161999702453613, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

## 状态

已完成

## 涉及范围

### 后端

- 新增 schema：`backend/modules/scene/schemas/scene_map_editor.py` → `SceneMapConfigParseResponse`（`resolution` / `start_point_x` / `start_point_y`）。
- 新增 service：`backend/modules/scene/services/scene_map_editor_service.py` → `SceneMapEditorService.parse_map_config(file_data)`，使用 `yaml.safe_load` 解析，校验 `resolution`、`origin` 必须存在且类型合法（origin 数组至少 2 个元素），缺失抛 `RequestError(400)`。仅读取解析，不落库。
- 新增接口：`backend/modules/scene/endpoints/scene_map_editor.py`（`scene_map_editor_public_router`）→ `POST /scene/map-editor/parse-map-config`，权限 `scene:map-editor:add` / `scene:map-editor:edit`，与 `/upload-image` 同组。
- 依赖：`backend/requirements.txt` 新增 `pyyaml>=6.0.1`（此前为 pydantic-settings 的传递依赖，现显式声明）。

### 前端

- 新增类型：`frontend/src/typings/api/scene.d.ts` → `Api.Scene.SceneMapConfigParseResult`。
- 新增 API：`frontend/src/service/api/scene.ts` → `fetchParseSceneMapConfig(file)`（multipart 上传）。
- 修改 `frontend/src/views/scene/map-editor/index.vue` 新增场景弹窗：
  - add 模式下「扫图起始点 X/Y」「分辨率」输入框 `:disabled="sceneDialogMode === 'add'"`。
  - add 模式下在「场景图片」下方新增「配置文件」`NUpload`（accept `.yaml,.yml`），解析成功后回显分辨率与起始点，并以 `NTag` 显示文件名。
  - edit 模式不变（仍可手填）。
  - add 模式未解析到起始点时，提交校验提示改为「请上传配置文件(yaml)以解析扫图起始点与分辨率」。

## 约束与备注

- 范围仅限**地图编辑器（map-editor）**新增场景弹窗；场景地图管理菜单（`scene/map` 的 operate-drawer）不动。
- 原 `scene/map/add` 接口与请求体未改动，仍接收 `resolution` / `start_point_x` / `start_point_y`，前端在提交前用解析结果填充这些字段。
- `origin` 第三项（yaw）忽略，仅取前两项作为 X/Y 起始点，与 `pixelToWorldCoords` / `worldToPixelCoords` 的原点语义一致（见 [[2026-06-30_map-editor-start-point-decouple-return-point]]）。
- 配置上传仅做解析回显，不在后端持久化文件。

## 相关文件

- `backend/modules/scene/schemas/scene_map_editor.py`
- `backend/modules/scene/services/scene_map_editor_service.py`
- `backend/modules/scene/endpoints/scene_map_editor.py`
- `backend/requirements.txt`
- `frontend/src/typings/api/scene.d.ts`
- `frontend/src/service/api/scene.ts`
- `frontend/src/views/scene/map-editor/index.vue`

## 记录日期

2026-07-02
