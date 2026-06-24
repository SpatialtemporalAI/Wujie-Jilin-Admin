# 机器人管理 gRPC 配置 + UI 隐藏 + 删除/权限修复

## 需求描述

围绕机器人管理与任务编辑的一组配套调整：

1. 在机器人管理中增加 agent / middleware 两套 gRPC 配置，单独权限控制，存为 robot 表 JSON 字段
2. 隐藏机器人管理列表中的「状态」按钮（保留代码以备恢复）
3. 隐藏机器人管理页面的搜索框（保留 searchParams 与 RobotSearch 文件以便恢复）
4. 修复删除机器人报错：关联 `robot_status_record` / `robot_voice_config` / `robot_event_log` 外键无级联，硬删触发约束失败
5. 修复编辑任务时弹「scene:map:list 无权限」：根因是编辑抽屉 `onMounted` 预加载 `fetchGetSceneMapList`，无权限用户被卡在 403

## 状态

已完成

## 涉及范围

### 任务 1：gRPC 配置

#### 后端

- `backend/database/models/business/robot.py`：Robot 新增 `grpc_config: Mapped[Optional[dict]]`（JSON）
- `backend/database/alembic/versions/0030_robot_grpc_config.py`：新迁移
  - `op.add_column("robot", grpc_config JSON)`
  - `bulk_insert sys_menu` 新增 BUTTON：id=3000000000000072, permission=`robot:manage:grpc_config`, parent=`robot_manage` 菜单
- `backend/modules/robot/schemas/robot.py`：
  - 新增 `GrpcServiceConfig`（host/port/enabled）
  - 新增 `RobotGrpcConfigPayload`（agent + middleware）
  - 新增 `RobotGrpcConfigUpdate`（包裹 grpc_config 字段，用于请求体）
  - `RobotResponseData` 新增 `grpc_config` 字段
- `backend/modules/robot/services/robot_service.py`：新增 `update_grpc_config(db, robot_id, grpc_config)`，单独事务
- `backend/modules/robot/endpoints/robot.py`：新增 `PUT /robot/manage/{robot_id}/grpc-config`
  - 权限 `require_permission("robot:manage:grpc_config")`
  - 与主表单 `robot:manage:edit` 完全解耦

#### 前端

- `frontend/src/typings/api/robot.d.ts`：新增 `GrpcServiceConfig` / `RobotGrpcConfig` 类型；`Robot` 类型新增 `grpc_config`
- `frontend/src/service/api/robot.ts`：新增 `fetchUpdateRobotGrpcConfig(id, data)`，PUT `/robot/manage/{id}/grpc-config`
- `frontend/src/views/robot/manage/modules/robot-grpc-config-drawer.vue`：新建独立弹窗
  - props: `visible` / `robotId`
  - watch visible 打开时 `fetchGetRobot` 拉取当前 grpc_config 回填
  - 表单分 Agent / Middleware 两块，各 host + port + enabled
  - 提交调 `fetchUpdateRobotGrpcConfig`
- `frontend/src/views/robot/manage/index.vue`：
  - 操作列新增「gRPC配置」按钮（权限 `robot:manage:grpc_config`）
  - 操作列宽度从 240 调整为 320
  - 新增 `grpcDrawerVisible` / `grpcDrawerRobotId` / `handleEditGrpc`
  - 模板挂载 `<RobotGrpcConfigDrawer>`

### 任务 2：隐藏状态按钮

- `frontend/src/views/robot/manage/index.vue`：操作列移除「状态」按钮（`hasAuth('robot:manage:list')` 那段）
- `RobotStatusDrawer` 组件与相关 ref/handler 保留，便于后续恢复

### 任务 3：隐藏搜索框

- `frontend/src/views/robot/manage/index.vue`：模板移除 `<RobotSearch>`，保留 `RobotSearch` import 与 `searchParams` reactive
- `frontend/src/views/robot/manage/modules/robot-search.vue`：文件保留

### 任务 4：修复删除机器人报错

- `backend/modules/robot/services/robot_service.py`：`RobotService.delete` 改为软删除并联动清理：
  - `robot_obj.deleted_at = now`（替代原来的 `db.delete(robot_obj)` 物理删除）
  - `update(RobotStatusRecord).where(robot_id=...).values(deleted_at=now)`
  - `update(RobotVoiceConfig).where(robot_id=...).values(deleted_at=now)`
  - `update(RobotEventLog).where(robot_id=...).values(deleted_at=now)`
  - 与项目其他模块（task_service.delete）一致使用 `soft_delete` 语义
- 新增 import：`RobotVoiceConfig` / `RobotEventLog` / `timezone` / `update`

### 任务 5：修复编辑任务触发 scene:map:list

- `frontend/src/views/task/modules/task-operate-drawer.vue`：
  - `loadMapOptions` 改为懒加载：加 `mapOptionsLoaded` 缓存标记；请求失败时静默返回空 options（不再阻断抽屉）
  - `onMounted` 移除 `loadMapOptions()` 调用
  - `<NSelect>` 场景地图下拉新增 `@focus="() => loadMapOptions()"`
  - `handleInitModel` 编辑模式下：从 `cloned.map_name` 或 `robots[0].map_name` 生成占位 option，避免无权限时下拉空白
  - 加载成功后若当前 map_id 不在返回列表中，仍保留占位项

## 关键决策

- **gRPC 字段结构**：统一 JSON 字段 `grpc_config`，内部 `{ agent, middleware }`，而非两个独立列
- **权限**：单一权限 `robot:manage:grpc_config`，与主表单 edit 解耦
- **前端入口**：列表新增「gRPC配置」操作按钮 + 独立弹窗（非主表单内嵌）
- **任务 5 修复**：懒加载 + 容错（不放宽后端权限，不新建接口）

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），未做 UI 测试
- 任务 2/3 是「隐藏」语义，相关代码保留以便快速恢复
- alembic 迁移链：`0029_grpc_retry_task_table` → `0030_robot_grpc_config`
- 权限按钮挂载在 `robot_manage` 菜单下（id=3000000000000003），与 robot:manage:list/add/edit/delete 同级
- `RobotResponseData.grpc_config` 使用 `RobotGrpcConfigPayload` 作为类型，Pydantic 会自动从 dict 反序列化

## 相关文件

后端：
- `backend/database/models/business/robot.py`
- `backend/database/alembic/versions/0030_robot_grpc_config.py`
- `backend/modules/robot/schemas/robot.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/modules/robot/endpoints/robot.py`

前端：
- `frontend/src/typings/api/robot.d.ts`
- `frontend/src/service/api/robot.ts`
- `frontend/src/views/robot/manage/index.vue`
- `frontend/src/views/robot/manage/modules/robot-grpc-config-drawer.vue`（新建）
- `frontend/src/views/task/modules/task-operate-drawer.vue`

## 记录日期

2026-06-24
