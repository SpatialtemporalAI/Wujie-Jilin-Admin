---
name: operation-monitor-status-latest-online
description: 运行监控页通过 /robot/{id}/status/latest 刷新机器人实时在线状态，并同步到前端机器人列表
type: business
---

# 2026-07-11 实时监控机器人在线状态刷新

## 需求

运行监控页需要**实时反映机器人当前在线状态**。在「实时监控」Tab 中，机器人下拉框、状态标签以及视频监控的启停都依赖 `robot.status`。原先 `robotList` 只在页面加载时拉取一次，机器人掉线/上线后页面不会刷新。

用户建议把在线状态更新放到 `/robot/{id}/status/latest` 接口中处理。

## 关键设计

- 后端 `/robot/{id}/status/latest` 每次被调用时，根据最新状态记录的更新时间判断机器人是否在线：
  - 记录在 60 秒内更新 → `online`
  - 无记录或记录超时 → `offline`
  - 机器人为 `inactive` 时，只有满足在线条件才升级为 `online`，否则保持 `inactive`
- 刷新后的状态会写回 `robot.status`（仅状态变化时 `commit`），并在响应中新增 `status` 字段返回。
  由于 `RobotStatusRecordResponseData` 继承 `BaseRespEntity`，必须覆盖 `status` 的 `field_serializer`，否则会被基类的 bool 序列化器转成 `"1"/"2"`；响应构造时通过 `model_validate({...字段, "status": status})` 传入 `status`，不能先 `model_validate(record)` 再赋值。
- 前端 `useRobotMonitor.refreshStatus` 在拿到 `status/latest` 响应后，把返回的 `status` 同步到 `robotList` 中对应机器人，使下拉框、视频监控等依赖项实时更新。

## 涉及文件

### 后端
- `backend/modules/robot/services/robot_status_record_service.py`
  - 新增 `STATUS_ONLINE_THRESHOLD_SECONDS = 60`
  - 新增 `get_latest_with_online_status()`：取最新记录并刷新 `Robot.status`
- `backend/modules/robot/schemas/robot_status_record.py`
  - `RobotStatusRecordResponseData` 新增 `status` 字段
- `backend/modules/robot/endpoints/robot_status_record.py`
  - `/{robot_id}/status/latest` 改为调用 `get_latest_with_online_status()`，并把状态回填到响应

### 前端
- `frontend/src/typings/api/robot.d.ts`
  - `RobotStatusRecord` 改为 `Omit<CommonRecord, 'status'> & { status: RobotStatusEnum; ... }`，避免与 CommonRecord 的 `EnableStatus` 冲突
- `frontend/src/views/operation-monitor/composables/useRobotMonitor.ts`
  - `refreshStatus()` 将 `data.status` 同步到 `robotList` 对应项

## 业务规则

1. 在线判定阈值暂定为 **60 秒**，以最新状态记录的 `updated_at`（不存在则用 `created_at`）为准。
2. 状态变更时写入数据库，避免前端每次轮询都触发 `commit`。
3. `inactive` 状态不会被自动改为 `offline`，避免覆盖管理员手动设置的未激活状态；但状态记录满足在线条件时会升级为 `online`。

## 关联记忆

- [[operation-monitor-livekit-video]] — 运行监控页视频监控 LiveKit 接入
- [[operation-monitor-video-switch-robot]] — 视频监控 Tab 切换机器人时先关旧再开新

## 记录日期

2026-07-11
