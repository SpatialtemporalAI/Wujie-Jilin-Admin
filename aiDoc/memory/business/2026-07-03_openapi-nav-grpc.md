# OpenAPI 导航补全 dedicated gRPC

## 需求描述

商户开放 API 的 `goto_point` / `navigate_route` 原实现是建一条临时 `patrol` Task + 复用 `RouteTaskService.NotifyTaskChanged(run_now)`。没有专门的导航 RPC，每次都要写库、污染 Task 表、API 调用与机器人动作无直接对应。

需求：为导航补一个 dedicated gRPC（`NavigationService`），OpenAPI 直接调用，不再走任务管线。机器人端同步实现，直接切换、不保留兜底。

> `speak` 不另造 RPC：经评估仍复用 `VoiceConfigService.TestTTSConfig`（`VoiceConfigClient.test_tts`）做即时播报，不新增 `Speak` RPC。

## 状态

已完成

## 改动总览

| 操作 | 改动前 | 改动后 |
|---|---|---|
| goto_point / navigate_route | 建临时 Task → `NotifyTaskChanged(run_now)` | `NavigationService.NavigateToPoint` / `NavigateRoute`（target=agent） |
| speak | `VoiceConfigService.TestTTSConfig` | **不变**（仍 `VoiceConfigClient.test_tts`） |

## 涉及范围

### 后端

- **proto**
  - 新建 `backend/grpc/protos/navigation/navigation.proto`（package `wujie.scene.navigation.v1`）：`service NavigationService { NavigateToPoint; NavigateRoute; }` + `NavigationPoint` / 4 个 Request/Response
  - `backend/grpc/protos/config/voice.proto`：仅注释补充「商户开放 API 的 speak 也复用 TestTTSConfig」，**未加 RPC**
- **生成**：`backend/grpc/main.py` 的 `modules` 追加 `"navigation"`；`cd backend/grpc && PYTHONUTF8=1 uv run python main.py` 重生成（Windows 控制台需 `PYTHONUTF8=1` 否则 emoji 打印触发 GBK 编码异常）
  - 产物：`backend/grpc/generated/navigation/navigation_pb2*.py`
- **包桥接**：新建 `backend/app/grpc/generated/navigation/__init__.py`，`__path__` 指向 `backend/grpc/generated/navigation`（与 config 桥接同构，上溯 5 层）
- **客户端**
  - 新建 `backend/modules/grpc/navigation_client.py`：`NavigationClient.navigate_to_point` / `navigate_route`，复用 `_dispatch_with_target` + `get_config_channel_by_addr`，`target="agent"`；`_build_point(dict)` 构造 `NavigationPoint`
  - `backend/modules/grpc/config_client.py`：**不动**（speak 仍用既有 `test_tts`）
- **业务接线** `backend/modules/merchant/services/openapi_service.py`
  - 删除 `_create_nav_task`（不再建临时 Task），新增 `_assert_points_on_robot_map(robot, annotations)`（地图归属校验）+ `_annotation_to_point(ann)`（→ point dict）
  - `goto_point` / `navigate_route` 改调 `NavigationClient.navigate_to_point` / `navigate_route`，按 `resp.success` 组装 `OpenApiResult`
  - `speak` **不动**（仍 `VoiceConfigClient.test_tts`）
  - 清理仅被旧导航逻辑使用的导入：`sqlalchemy.insert`、`TaskPoint`（`Task`/`task_robot_association` 仍被 `list_tasks` 用，保留）

### 前端

- 无改动（纯后端 gRPC 契约补全）

## 关键决策

- **导航走 agent**：导航是机器人运动指令，与任务执行/TTS 一致走 `target="agent"`（非 middleware）。机器人端按 `robot.grpc_config.agent` 地址解析。
- **导航请求带全量点位**：`NavigateToPointRequest` 内嵌 `NavigationPoint{point_id,name,x,y,angle}` + `map_id`，机器人侧无需回查后端（对齐 `NotifyMapSaved` 内嵌 `MapInfo` 的全量风格）。
- **speak 不新增 RPC**：评估后认为 `TestTTSConfig` 入参（voice/speed/volume/text）已能覆盖即时播报，再造 `Speak` RPC 收益有限，保持复用。
- **复用 `_dispatch_with_target` 内核**：ENABLED 短路、地址解析、stub 按 addr 缓存、超时、异常吞掉返回 `success=False` 哨兵——与 voice/task/speed/battery 客户端一致，失败不冒泡 500。
- **直接切换不兜底**：用户确认机器人端同步实现 `NavigationService`，OpenAPI 不保留任务式回退。
- **路由完全在 channel/addr 层**：导航 proto 不含 robot_id 路由字段，target=agent 由客户端 `_dispatch_with_target` 解析（与 SwitchMap/NotifyMapSaved 一致）。

## 约束与备注

- 生成脚本 `main.py` 在 Windows 下打印 `✅`/`❌` emoji 会触发 `UnicodeEncodeError: 'gbk'`；必须 `PYTHONUTF8=1 uv run python main.py`（脚本本身逻辑不受影响，仅控制台编码）
- `openapi_service.py` 的 `ConflictError` 导入为**改动前已存在**的未用导入，本次未处理以保持 diff 聚焦
- 关联 [[2026-06-29_merchant-openapi]]（OpenAPI 总契约）、[[2026-07-03_map-grpc-to-middleware]]（同类「按 robot.grpc_config 地址下发」路由模式）

## 相关文件

后端：
- `backend/grpc/protos/navigation/navigation.proto`（新建）
- `backend/grpc/protos/config/voice.proto`（仅注释）
- `backend/grpc/main.py`
- `backend/grpc/generated/navigation/navigation_pb2*.py`（生成）
- `backend/app/grpc/generated/navigation/__init__.py`（新建桥接）
- `backend/modules/grpc/navigation_client.py`（新建）
- `backend/modules/merchant/services/openapi_service.py`

文档：
- `aiDoc/frontend-backend/boundary.md`（OpenAPI→gRPC 映射表已更新：导航列改 NavigationService，speak 仍 TestTTSConfig）

## 记录日期

2026-07-03
