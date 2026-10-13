# 任务变更通知 NotifyTaskChanged 增加 execution_id

## 需求描述

执行列表里同名任务多行（同一 task_id 下多条 task_execution_record），原 `TaskChangedRequest` 只有 `task_id` + `operation`，机器人无法区分「是哪一行」，只能按 `updated_at` 猜最近一条，与平台按 `start_time` 排序展示的顺序无关，导致「恢复第 3 行结果第 1 行跑了」。

修复：`TaskChangedRequest` 新增 `int64 execution_id = 3`，值 = 用户选中行的 `task_execution_record.id`；`0` = 未指定，机器人走原兜底逻辑。

## 状态

已完成

## 涉及范围

### 后端

- proto（子模块 `backend/grpc`，即 Wujie-Jilin-Grpc 仓库）：`protos/task/task.proto` 的 `TaskChangedRequest` 新增 `execution_id = 3`（字段号 1/2 不动），`uv run python main.py` 重新生成 stub；`app.grpc.generated.task` 经 path bridge 指向子模块生成文件，无需复制
- `modules/grpc/task_client.py`：`notify_task_changed` / `broadcast_task_changed` 新增 `execution_id: int = 0` 参数，写入 request 与 log_ctx
- `modules/task/services/task_execution_record_service.py`：
  - `pause_execution` / `resume_execution` / `stop_execution` 带 `execution_id=record.id`
  - `pause_executions_by_task` 由「按 robot 聚合一次广播」改为「逐条记录推送，各带自己的 execution_id」
  - `start_execution`（run_now）无执行记录上下文，传默认 0
- `task_service.py` 的 create/edit/delete/enable/disable 走默认 0，零改动

### 前端

无需改动：暂停/恢复/停止接口本来就按 `record_id` 路径参数调用。

## 约束与备注

- protobuf 字段号是上线合同：只加 `3`，不重排、不改已有字段号/类型
- 兼容性：老机器人忽略未知字段 3；机器人先上、平台传 0 时走原兜底逻辑；两边可任意顺序发布、可灰度
- 机器人对 `execution_id > 0` 但取不到（不属该 task / 已删 / 已取消 / 不存在）返回 `success=false, message="Execution <id> not found for task <task_id>"`；本平台侧**保持仅记日志**不阻塞（DB 状态已先提交），不向用户报错
- 活跃执行列表已按 `id.desc()` 排序（`build_active_query`），天然满足「排序字段不被恢复动作改写」的建议，无需改
- git 提交顺序：先在子模块 `backend/grpc` 提交 proto + 生成文件，再在主仓库提交子模块指针与业务代码

## 相关文件

- `backend/grpc/protos/task/task.proto`
- `backend/grpc/generated/task/task_pb2.py`、`task_pb2_grpc.py`（重新生成）
- `backend/modules/grpc/task_client.py`
- `backend/modules/task/services/task_execution_record_service.py`
- 参考文档：`平台对接-execution_id-说明.md`（2026-10-13）

## 记录日期

2026-10-13
