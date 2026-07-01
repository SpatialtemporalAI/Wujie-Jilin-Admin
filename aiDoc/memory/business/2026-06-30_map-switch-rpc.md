# map.proto 新增 SwitchMap 方法：切换机器人当前地图

**日期**: 2026-06-30
**提出者**: 用户

## 需求描述

在 `backend/grpc/protos/map/map.proto` 的 `MapService` 新增一个 RPC 方法，用于切换机器人当前所在的地图（通知导览服务把机器人当前活动地图切换到指定地图）。

## 契约设计（与用户确认）

- **请求结构**：只带目标地图标识 `id` + `version`（与现有 `MapSummary` / `SearchMaps` 的标识约定一致），机器人从已缓存地图中切换。**不**推送完整 `MapInfo`。
- **地址**：与「广播地图」(NotifyMapSaved) 共用同一个 MapService stub / channel 地址（`MapServiceClient._stub_()` → `get_map_service_addr()` = `settings.GRPC.MAP_SERVICE_ADDR` 或运行时覆盖）。

## 状态

已完成（平台侧 proto + client + 切换地图接口接入；机器人/导览服务端需按契约实现 `SwitchMap` handler）

## 涉及范围

### proto（`backend/grpc/` 子仓库）

- `protos/map/map.proto`：`MapService` 新增 `rpc SwitchMap(SwitchMapRequest) returns (SwitchMapResponse);`
  - `SwitchMapRequest { string id = 1; string version = 2; }`
  - `SwitchMapResponse { string status = 1; string message = 2; string current_id = 3; string current_version = 4; }`（回显切换后当前地图）
- `generated/map/map_pb2.py` / `map_pb2_grpc.py`：重新生成（`PYTHONUTF8=1 uv run python main.py`，Windows 控制台 GBK 编码下 emoji 打印会崩，必须设 UTF-8）

### 平台后端

- `backend/modules/grpc/client.py`：`MapServiceClient.switch_map(map_id, version)` 类方法，沿用既有模式（`settings.GRPC.ENABLED` 关闭时返回 `status="DISABLED"`，`timeout=settings.GRPC.TIMEOUT_SECONDS`），`id/version` 内部 `str()` 强转对齐 proto string 字段。与 `notify_map_saved` 共用同一 stub，故 gRPC 地址相同。
- `backend/modules/robot/services/robot_service.py`：切换地图接口 `update_map_binding`（对应 `PUT /robot/manage/{robot_id}/bind-map`，地图编辑器专用）在绑定成功（`db.commit` 后）且 `map_id is not None` 时，调用新增的 `_switch_map_via_grpc(map_id, version)` 下发 SwitchMap。解绑（`map_id=None`）不下发。失败仅记日志、不抛出（沿用「广播地图」`_notify_map_saved` 模式），导览服务不可用不回滚绑定。原 SceneMap 存在性校验顺带保留对象以读 `version`。

## 关键业务规则

- 标识维度：地图以 `id`（SceneMap.id）+ `version`（SceneMap.version）标识，与 `NotifyMapSaved` / `SearchMaps` 一致；proto 中均为 `string`。
- 客户端方法 `id/version` 接受 `str | int`，调用方可直接传 SceneMap 的整型 id/version。
- 切换地图 = 机器人绑定/改绑场景地图（`robot.map_id` 变更）；仅在绑定新地图时下发 SwitchMap，解绑不下发。

## 约束与备注

- 仅平台侧 proto + client + 切换地图接口接入；机器人端导览服务的 `SwitchMap` 实现不在本仓库。
- 重新生成时顺带把 `generated/task/task_pb2_grpc.py` 与 `task.proto` 已提交但生成的旧文件做了 docstring 同步（pause/resume/stop 注释），为良性副产物。
- `backend/grpc` 是独立 git 仓库（子模块），生成文件归其管理；主仓库通过 `app/grpc/generated/map/__init__.py` 路径桥接引用 `backend/grpc/generated/map/`。
- 验证：`py_compile client.py` / `robot_service.py` 通过；`map_pb2.SwitchMapRequest/Response` 字段读写 smoke-test 通过；`map_pb2_grpc.MapServiceStub` 实例含 `SwitchMap`（与 `NotifyMapSaved`/`SearchMaps` 一样在 `__init__` 绑定，类属性 `hasattr` 为 False 属正常）。

## 相关文件

- `backend/grpc/protos/map/map.proto`
- `backend/grpc/generated/map/map_pb2.py`
- `backend/grpc/generated/map/map_pb2_grpc.py`
- `backend/modules/grpc/client.py`
- `backend/modules/robot/services/robot_service.py`（`update_map_binding` + `_switch_map_via_grpc`）
- `backend/modules/robot/endpoints/robot.py`（`PUT /{robot_id}/bind-map`，未改）

## 相关历史记忆

- [2026-06-18 NotifyMapSaved image_url 内部 token](./2026-06-18_notify-map-saved-image-url-internal-token.md)（MapService 既有 NotifyMapSaved 推送完整 MapInfo 的约定）

## 记录日期

2026-06-30
