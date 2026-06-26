# 机器人 gRPC 配置新增 ros 选项

## 需求描述

在机器人管理的 gRPC 配置弹窗中，在原有 agent / middleware 两套配置之外，再新增一套 ros 配置（host + port + enabled），统一存入 robot.grpc_config JSON 字段。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/robot/schemas/robot.py`
  - `RobotGrpcConfigPayload` 新增 `ros: Optional[GrpcServiceConfig]` 字段
  - `RobotResponseData.grpc_config` 描述更新为 `{ agent, middleware, ros }`
  - 历史脏数据兜底 `_sanitize_grpc_config` 的清洗键列表加入 `"ros"`，避免库里有半截 ros 子对象导致列表序列化 422
- `backend/modules/robot/services/robot_service.py`：`update_grpc_config` docstring 改为 agent / middleware / ros
- `backend/modules/robot/endpoints/robot.py`：`PUT /robot/manage/{robot_id}/grpc-config` docstring 同步
- 复用已有 `robot:manage:grpc_config` 按钮权限，不新增权限点

### 前端

- `frontend/src/typings/api/robot.d.ts`
  - `RobotGrpcConfig` 新增 `ros?: GrpcServiceConfig | null`
  - `Robot.grpc_config` 注释改为 `agent + middleware + ros`
- `frontend/src/service/api/robot.ts`：`fetchUpdateRobotGrpcConfig` 注释更新
- `frontend/src/views/robot/manage/modules/robot-grpc-config-drawer.vue`
  - `FormModel` 新增 `ros: ServiceFormModel`
  - `createDefaultModel` / `loadRobot` 回填 / `handleSubmit` payload 同步加 ros
  - 校验规则新增 `ros.host` / `ros.port`
  - 模板在 Middleware 区块后追加 ROS 区块（服务地址 / 服务端口 / 启用）

## 关键决策

- **不加迁移**：`grpc_config` 本就是 JSON 字段，扩展子键无需 DDL
- **不加权限**：ros 与 agent / middleware 共用同一弹窗与同一权限 `robot:manage:grpc_config`
- **回填兼容旧数据**：没有 ros 字段的 robot，前端默认 `host='' / port=null / enabled=false`，后端 `Optional` 直接放行

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），未做 UI 测试
- 与 [[2026-06-24_robot-manage-grpc-config-and-fixes]] 同源扩展，结构对齐

## 相关文件

后端：
- `backend/modules/robot/schemas/robot.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/modules/robot/endpoints/robot.py`

前端：
- `frontend/src/typings/api/robot.d.ts`
- `frontend/src/service/api/robot.ts`
- `frontend/src/views/robot/manage/modules/robot-grpc-config-drawer.vue`

## 记录日期

2026-06-25
