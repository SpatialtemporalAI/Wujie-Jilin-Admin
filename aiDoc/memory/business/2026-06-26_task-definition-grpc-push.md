# 任务定义变更 gRPC 推送（create/edit/delete）

## 需求描述

任务管理「任务列表」中，新增 / 编辑 / 删除任务时，需要通过 gRPC 通知机器人 agent，
让 agent 端感知任务定义变更（重新加载/取消调度等）。

此前（2026-06-26）已为运行时控制（start/pause/resume/stop）接入 gRPC，
但 create/edit/delete 任务定义变更一直未推送。本次补全这一块。

## 状态

已完成

## 涉及范围

### 后端

修改：`backend/modules/task/services/task_service.py`

- 顶部 import `TaskConfigClient`（来自 `modules.grpc.task_client`）
- `TaskService.create` —— commit 后 broadcast `operation="create"`，robot_ids 来自 `task_in.robot_ids`
- `TaskService.update` —— commit 后 broadcast `operation="edit"`：
  - 若请求带了 `task_in.robot_ids` → 用请求值
  - 若未带 → 查 `task_robot_association` 当前关联 robot_ids
- `TaskService.delete` —— 软删除前先取出 `task_robot_association` 关联 robot_ids，
  commit 后 broadcast `operation="delete"`

### 前端

无变更。

## 关键决策

### 复用现有 TaskConfigClient，不新增 proto 字段

`task.proto` 的 `string operation` 早就是字符串自由取值，注释里已经列了
`create / edit / delete / enable / disable / run_now / pause / resume / stop`，
只是后端 service 层没调。本次只补 service 调用，不动 proto、不重新生成 pb2。

### 不接 GrpcRetryService 重试队列

与 2026-06-26 task-execution-grpc-push 的决策一致：
推送失败仅 `logger.warning`，不入 `grpc_retry_task` 队列。
后续如需重试，可在 service 层失败分支入队，
并在 `retry_service.py` 的 `_ROUTING` 表加 `("route_task", "NotifyTaskChanged")` 路由。

### 不覆盖 enable/disable

用户本次只说「新增删除编辑」，toggle enabled 的 gRPC 推送不在范围内。
proto 注释已留好 `enable/disable` 取值，后续如需要再补。

### 放 service 层而非 endpoint 层

跟项目惯例对齐（`task_execution_record_service.py`、`robot_config_service.py`
所有 gRPC 推送都在 service 层）。定时任务/内部调用若复用这些 service 方法，
也能自动带上推送。

## 验证

### 静态检查（已通过）

```
python -m py_compile modules/task/services/task_service.py
```

### 端到端

- **新增任务**：`POST /task/manage/add` → DB 写入 + 日志出现 `grpc task notify`
  相关记录（无 agent 时 `success=False`，业务流程不阻塞）
- **编辑任务**：`PUT /task/manage/{task_id}` → 同上，operation=edit
- **删除任务**：`DELETE /task/manage/{task_id}` → 同上，operation=delete，
  且推送发生在软删除之后

## 相关文件

- `backend/modules/task/services/task_service.py`（修改）
- `backend/modules/grpc/task_client.py`（复用，无修改）
- `backend/grpc/protos/task/task.proto`（无修改，注释里已列 create/edit/delete）

## 记录日期

2026-06-26
