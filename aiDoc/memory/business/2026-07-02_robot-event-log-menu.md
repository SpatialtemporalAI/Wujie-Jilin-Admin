# 机器人事件日志挂到日志管理菜单

## 需求描述

将机器人事件日志（`robot_event_log`）入口增加到「日志管理」目录下，界面参考「操作日志」。
用户反馈该入口在日志管理菜单中不可见。

## 状态

已完成

## 调研结论

该功能在提出需求前已基本全栈实现，**唯一缺口是 `sys_menu` 种子数据**：

- 后端：`RobotEventLog` 模型、`RobotEventLogService`、schema、5 个接口（list/detail/batch-delete/clear/single-delete）均存在，路由已在 `backend/modules/robot/router.py` 注册（前缀 `/robot/event-log`）。Alembic 建表迁移 `0010_robot_event_log`。
- 前端：页面 `frontend/src/views/log/robot-log/index.vue`、搜索组件 `robot-event-log-search.vue`、`service/api/log.ts` 中的 5 个 API、`system-manage.d.ts` 类型、`zh-cn.ts`/`en-us.ts` i18n（含 `route.log_robot-log` 与 `page.log.robotEventLog.*`）、elegant-router 路由（`log_robot-log` → `/log/robot-log`）均存在。
- 缺口：登录/操作/在线用户日志都有 `sys_menu` 种子（见 `0002_seed_data.py`），唯独 `log_robot-log` 没有，故动态菜单下不显示。

## 涉及范围

### 后端

- 新增迁移 `backend/database/alembic/versions/0039_seed_robot_event_log_menu.py`
  - 在「日志管理」目录（id=`2874692539129858`）下插入 1 个 MENU + 2 个 BUTTON：
    - MENU `log_robot-log`（permission `robot:monitor:list`，与列表接口权限一致）
    - BUTTON `log_robot-log_list`（permission `robot:monitor:list`）
    - BUTTON `log_robot-log_delete`（permission `robot:event-log:delete`）
  - 菜单 ID：`3000000000000100/101/102`（新分配，避开既有占用）
  - 沿用 `0011_operation_monitor_menu` 的列定义（不写 `meta_icon_type`，由 server_default '1' 兜底），且不插 `sys_role_menu`（超管自动可见全部菜单；非超管角色通过角色管理 UI 分配，与 0011/0034/0036 一致）。
  - `down_revision = 0038_robot_face_entity`（升级后为唯一 head）。

### 前端

- 无代码改动（页面/路由/i18n/API 已就绪）。

## 约束与备注

- 列表接口权限为 `robot:monitor:list`，删除/清理为 `robot:event-log:delete`；菜单与按钮 permission 必须与接口一致，否则按钮可见但调用 403，或菜单不显示。
- 部署需执行 `alembic upgrade head` 生效；非超管角色需在「角色管理」勾选该菜单。

## 相关文件

- `backend/database/alembic/versions/0039_seed_robot_event_log_menu.py`（新增）
- `backend/modules/robot/endpoints/robot_event_log.py`
- `frontend/src/views/log/robot-log/index.vue`
- `frontend/src/service/api/log.ts`

## 记录日期

2026-07-02
