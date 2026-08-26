# 机器人卡片「服务器自启状态 + 重启」

## 需求描述

1. 机器人管理卡片底部新增「服务器自启状态」行：状态 Tag + 「重启」按钮。
2. 数据来源为外部机器人控制面板 HTTP 接口（查 5090 上 zenoh/middleware/大脑层是否起来，**不是** 50051 RobotServiceManager）：
   - `GET {BASE}/api/slot-status?robot_id=...&serial_number=...` → `{"status":"已启动"|"启动中"|"启动失败"}`，超时 5s
   - `POST {BASE}/api/slot-restart`，body `{"robot_id":"...","serial_number":"..."}` → 同格式返回
   - 每次必带同一台的 `robot_id` + `serial_number`（对不上即「启动失败」）
3. 面板地址必须可配置（后端 `.env`），不写死。

## 状态

已完成（后端 + 前端 + .env 配置 + py_compile/typecheck 通过；面板联通属外部环境未实测）

## 涉及范围

### 后端

- **配置**：`core/config/settings_model.py` 新增 `RobotPanelModel`（`BASE_URL` 默认空、`TIMEOUT_SECONDS` 默认 5）；`settings.py` 挂 `ROBOT_PANEL`；环境变量 `ROBOT_PANEL__BASE_URL=http://192.168.112.198:5678` 已追加到 `.env`/`.env.dev`/`.env.test`/`.env.prod`。
- **Service**：`modules/robot/services/robot_slot_service.py`（httpx.AsyncClient）。`get_slot_status`：地址未配置返回「未配置」，网络异常返回「未知」（不拖垮列表）；`restart_slot` 网络异常抛 `ServerError`。
- **Endpoints**：`modules/robot/endpoints/robot.py` 新增 `GET /manage/{robot_id}/slot-status`（权限 `robot:manage:list`）、`POST /manage/{robot_id}/slot-restart`（复用 `robot:manage:edit`，避免新增菜单种子；带 `@log_operation` action=restart）。
- **Schema**：`modules/robot/schemas/robot.py` 新增 `SlotStatusData`（**不能用 BaseRespEntity**，其 status 序列化器会把 truthy 值转成 "1"）。

### 前端

- 类型 `typings/api/robot.d.ts`：`SlotStatus` / `SlotStatusData`；API `service/api/robot.ts`：`fetchGetRobotSlotStatus` / `fetchRestartRobotSlot`。
- 页面 `views/robots/index.vue`：卡片新增 `robot-card-slot` 行（虚线分隔，左标签右 Tag+重启按钮）；列表加载后并行拉各台状态（单台失败置「未知」）；重启按钮 loading + `启动中` 时 disabled，成功后刷新该台状态；状态色：已启动=success/启动中=warning/启动失败=error/其它=default；按钮权限 `robot:manage:edit`。

## 约束与备注

- 「启动中」只轮询查询、不要再重启；重启后最多等约 70s（当前前端未做自动轮询，由用户手动刷新/再点查看）。
- 面板真机不在时不拉进程，会返回「启动失败」。

## 相关文件

- `backend/core/config/settings_model.py`、`backend/core/config/settings.py`
- `backend/modules/robot/services/robot_slot_service.py`、`backend/modules/robot/endpoints/robot.py`、`backend/modules/robot/schemas/robot.py`
- `frontend/src/typings/api/robot.d.ts`、`frontend/src/service/api/robot.ts`、`frontend/src/views/robots/index.vue`

## 记录日期

2026-08-26
