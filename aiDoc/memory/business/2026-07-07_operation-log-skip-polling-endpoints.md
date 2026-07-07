# 高频轮询接口不写操作日志（robot-locations / status/latest / export/task/list）

## 需求描述

`robot_location`、`robot/status/latest`、导出任务列表三个高频轮询接口不需要写入操作日志（SysOperationLog），避免日志被高频读请求淹没。

## 状态

已完成（后端 1 文件）。`py_compile` 通过；匹配逻辑验证三个目标命中、易混淆路径（机器人增删改、导出提交/状态/下载、其他模块）不误伤。

## 涉及范围

### 后端

- `backend/core/middleware/operation_log_middleware.py`：
  - 原有 `WHITELIST_PREFIXES`（前缀匹配，排除 auth / operation-log / login-log / monitor / docs 等）保持不变。
  - 新增 `WHITELIST_SUFFIXES` 后缀匹配元组；`_is_whitelisted` 改为同时检查前缀和后缀。
  - 三个排除项：`/robot-locations`、`/status/latest`、`/export/task/list`。

### 前端

无。

## 约束与备注

- **为什么用后缀匹配而不是前缀**：两个 robot 接口带动态路径参数（`/admin/robot/manage/map/{map_id}/robot-locations`、`/admin/robot/manage/{robot_id}/status/latest`），若用 `/admin/robot/manage/` 前缀会误伤同前缀的机器人增删改（那些必须记录）。后缀 `/robot-locations`、`/status/latest` 经 grep 确认全项目唯一，不会误伤。
- 导出列表 `/admin/sys/export/task/list` 用后缀 `/export/task/list`，不会误伤导出提交（POST `/task`）、状态查询（`/task/{id}`）、下载（`/task/{id}/download`）。
- 操作日志中间件只拦截 `/admin/` 前缀且不在白名单的请求；记录走异步 `BackgroundTask`，失败仅日志不影响主请求。
- `export/task/list` 与 [2026-07-06 日志导出 Excel](./2026-07-06_log-export-excel.md) 的下载箱轮询是同一接口；与 [2026-07-07 导出任务卡死修复](./2026-07-07_export-task-stuck-recover-and-timeout.md) 同属导出体系。

## 相关文件

- `backend/core/middleware/operation_log_middleware.py`（改）
- `backend/modules/robot/endpoints/robot_status_record.py`（未改，被排除的两个接口定义处：`/{robot_id}/status/latest`、`/map/{map_id}/robot-locations`）
- `backend/modules/admin/endpoints/sys/export_task.py`（未改，被排除的列表接口定义处：`/task/list`）

## 记录日期

2026-07-07
