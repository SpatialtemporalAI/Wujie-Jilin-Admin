# 任务执行 gRPC 推送补全

## 需求描述

任务管理「手动执行」与「定时执行」此前仅完成平台侧 DB 状态流转，
机器人 agent 端拿不到任何"该开始/暂停/恢复/停止任务"的实时信号。

需要：在 start（手动+定时）/ pause / resume / stop 四类操作后，
按任务关联的 robot_ids 逐个通过 gRPC 通知到对应 agent。

## 状态

已完成

## 涉及范围

### 新建

- `backend/app/grpc/generated/task/__init__.py`
  - path bridge，把 `app.grpc.generated.task` 的 `__path__` 指向
    git 子模块 `backend/grpc/generated/task/`
  - 让 `task_pb2_grpc.py` 内硬编码的
    `import app.grpc.generated.task.task_pb2` 能解析到（沿用 config / map 同款模式）

- `backend/modules/grpc/task_client.py`
  - `TaskConfigClient` 类，类方法风格
  - `notify_task_changed(robot_id, task_id, operation)` 单 robot 推送，走 target=agent
  - `broadcast_task_changed(task_id, operation, robot_ids)` 按 robot_ids 逐个推送并聚合结果
  - 复用 `config_client._dispatch_with_target` 通用调度内核、
    `RobotConfigAddrProvider` 地址解析、`get_config_channel_by_addr` channel 缓存
  - 失败仅返回 `success=False` 哨兵，不抛异常

### 修改

- `backend/grpc/protos/task/task.proto`
  - 注释补充 pause / resume / stop 三个运行时 operation 取值（不改 schema，仅注释）
  - `string operation` 字段注释更新为
    `create / edit / delete / enable / disable / run_now / pause / resume / stop`

- `backend/modules/task/services/task_execution_record_service.py`
  - 顶部 import `TaskConfigClient`
  - 6 处 service 方法 commit 后接入推送：
    - `start_execution` → broadcast `run_now` + `payload.robot_ids`
    - `start_or_resume_execution` resumed 分支 → broadcast `resume` + paused_records 的 robot_ids
    - `pause_execution` → broadcast `pause` + `[record.robot_id]`
    - `pause_executions_by_task` → broadcast `pause` + 所有匹配 records 的 robot_ids
    - `resume_execution` → broadcast `resume` + `[record.robot_id]`
    - `stop_execution` → broadcast `stop` + `[record.robot_id]`
  - 推送位置：service 层（跟随项目惯例，对齐 robot_config_service 的 grpc 推送模式）
  - 推送失败仅 `logger.warning`，不抛异常、不回滚 DB、不阻塞响应

## 关键决策

### 放 service 层而非 endpoint 层

- 项目惯例（`robot_config_service.py:209` 起）所有 grpc 推送都在 service 层
- 放 service 层后，定时任务 `scan_scheduled_tasks.py` 直接调
  `start_or_resume_execution` 即可复用推送路径，无需单独改
- AGENTS.md 的"Service 层不要依赖 FastAPI 请求对象"不冲突 —— grpc 不属于 HTTP 请求对象

### operation 取值约定

proto 的 `string operation` 不限制枚举，直接传字符串：
- `run_now` —— start（手动 + 定时）
- `pause` —— pause
- `resume` —— resume
- `stop` —— stop

不改 proto schema、不重新生成 pb2 代码，机器人 agent 端按字符串匹配处理。

### 不接入重试基建

- 按用户决策：本次失败仅日志，不入 `GrpcRetryService.save_pending` 队列
- 后续如需重试，可参考 `_ROUTING` 表（`retry_service.py:44`）扩展
  `("route_task", "NotifyTaskChanged")` 路由 + 在 service 层失败分支入队

### 不覆盖任务定义变更

- 本次仅覆盖运行时控制（start / pause / resume / stop）
- create / edit / delete / enable / disable 任务定义变更暂不推送（proto 设计原意）
- 如后续机器人 agent 需要感知任务定义变更，再单独扩展

## 验证方案

### 静态检查（已通过）

```
python -c "from app.grpc.generated.task import task_pb2, task_pb2_grpc; \
from modules.grpc.task_client import TaskConfigClient; \
from modules.task.services.task_execution_record_service import TaskExecutionRecordService"
python -m py_compile modules/task/services/task_execution_record_service.py \
  modules/grpc/task_client.py app/grpc/generated/task/__init__.py
```

### 端到端

- **手动 start**：调 `POST /task/execution-record/{task_id}/start`
  - 预期：DB 出现 running 记录，接口 200，日志出现 `grpc task notify` 相关记录
  - 无 agent 场景：grpc 调用返回 `success=False`（连接失败或地址未配置），但业务流程不受影响
- **定时 start**：调整某 task 的 `schedule_start_time` 为下一分钟
  - 预期：scan_scheduled_tasks 日志后跟随 grpc 推送日志
- **pause / resume / stop**：分别调对应接口
  - 预期：每次接口返回后日志出现对应 operation 的推送记录

## 相关文件

后端：
- `backend/app/grpc/generated/task/__init__.py`（新建）
- `backend/modules/grpc/task_client.py`（新建）
- `backend/grpc/protos/task/task.proto`（注释补充）
- `backend/modules/task/services/task_execution_record_service.py`（6 处推送接入）

## 记录日期

2026-06-26
