# 任务定时配置真正落库（schedule_date / schedule_start_time）

**日期**: 2026-06-30
**提出者**: 用户

## 需求描述

任务管理新增/编辑任务时：
1. **勾选「启用定时执行」后，调度日期、开始时间必填，重复周期选填**（校验此前已存在，本次确认仍生效）。
2. **定时配置此前没有保存到数据库**——`schedule_enabled` / `schedule_repeat_cycle` 会落库，但 `schedule_date` / `schedule_start_time` 从未提交给后端，外部调度程序读到的是空值。

## 背景（关键）

`Task.schedule_*` 字段是**本服务与外部调度程序的契约**：本服务自身的定时扫描器已于 2026-06-29 移除（见 [2026-06-29 移除本服务定时调度](./2026-06-29_task-schedule-removed-and-start-grpc-only.md)），调度执行改由外部程序负责，外部程序通过读取 `task.schedule_*` 字段决定何时触发。因此**前端必须把完整的 schedule 配置写入 DB**，否则外部程序拿不到日期/时间。后端 model / `TaskCreate` / `TaskUpdate` / `TaskResponseData` 的 `schedule_*` 字段早已就绪，问题纯粹在前端。

## 状态

已完成

## 涉及范围

### 后端

`backend/modules/task/schemas/task.py` 的 `TaskResponseData`：`schedule_date` / `schedule_start_time` 由 `Optional[str]` 改为 `Optional[date]` / `Optional[time]`。

> 原因：前端落库后这两个字段首次出现非空值，暴露出响应序列化的潜在 bug——ORM 列是 `Date`/`Time`，运行时持有 `datetime.date`/`datetime.time` 对象，而响应 schema 写成 `Optional[str]`，pydantic v2 严格模式不会把 `date`/`time` 隐式转 `str`，`TaskResponseData.model_validate(task_obj)` 直接报 `Input should be a valid string` → 接口 422。此前字段恒为 `None` 故一直没暴露。改为 `Optional[date]`/`Optional[time]` 后，pydantic 正常校验并把它们序列化成 JSON 字符串（`yyyy-MM-dd` / `HH:mm:ss`），与前端 `string | null` 契约一致。model / service / endpoint 无需改动。

### 前端

仅 `frontend/src/views/task/modules/task-operate-drawer.vue`：

- **根因**：`handleSubmit` 构造的 `submitData` 只放了 `schedule_enabled` / `schedule_repeat_cycle`，漏掉 `schedule_date` / `schedule_start_time` → 永不落库。
- **类型不一致**：原 `FormModel.schedule_date` / `schedule_start_time` 为 `number | null`（NDatePicker/NTimePicker 的时间戳），而后端期望 ISO 字符串（`date` → `yyyy-MM-dd`，`time` → `HH:mm:ss`）。
- **修复方式**（不改动 picker 的 `value-format`，因为 naive-ui 2.43.2 的 `NDatePicker`/`NTimePicker` 类型定义里 `value` 仍强制为 `number`，加 `value-format` 会让 `string` 模型类型检查不过）：
  - 引入 `dayjs`，新增 4 个转换函数：`dateStrToTs` / `timeStrToTs`（编辑回填 字符串→时间戳）、`tsToDateStr` / `tsToTimeStr`（提交 时间戳→字符串）。
  - `handleInitModel` 编辑分支：用 `dateStrToTs` / `timeStrToTs` 把后端返回的 `schedule_date` / `schedule_start_time` 字符串回填到 picker。
  - `handleSubmit` 的 `submitData`：补上 `schedule_date` / `schedule_start_time`，并按 `schedule_enabled` 取值——**未启用时三个 schedule 字段统一置 `null`**，避免残留脏数据。

## 关键业务规则

- 勾选「启用定时执行」：调度日期、开始时间**必填**；重复周期（周一~周日 多选）**选填**（未选即不重复/单次）。
- 未勾选时：`schedule_date` / `schedule_start_time` / `schedule_repeat_cycle` 提交时一律 `null`。
- 时间精度：`schedule_start_time` 精确到分钟（显示 `HH:mm`），落库存 `HH:mm:ss`。
- 重复周期存储格式：逗号分隔的星期值 `mon,tue,...,sun`（后端 `_validate_repeat_cycle` 校验合法集合）。

## 约束与备注

- 不引入新的 DB 字段、不做表结构变更，完全复用现有 `Task.schedule_*` 列。
- 不改后端；契约字段（`Api.Task.TaskCreate.schedule_date?` 等）类型本就是 `string | null`，无需改 `task.d.ts`。
- 验证手段：`pnpm typecheck`（项目约定前端变更只做 typecheck，不做界面测试）。

## 相关文件

- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `backend/modules/task/schemas/task.py`（`TaskResponseData.schedule_date`/`schedule_start_time` 改为 `Optional[date]`/`Optional[time]`）
- `backend/database/models/business/task.py`（未改动，字段已存在）
- `backend/modules/task/services/task_service.py`（未改动，create/update 已写入字段）

## 相关历史记忆

- [2026-06-29 移除本服务定时调度 + 启动改纯 gRPC](./2026-06-29_task-schedule-removed-and-start-grpc-only.md)（schedule_* 字段保留作外部调度程序契约，本次修复前端落库）
- [2026-06-24 定时扫描调度任务](./2026-06-24_task-schedule-scan.md)（已移除的扫描器，定义了 schedule 命中规则，外部程序应沿用相同语义）
- [2026-06-17 任务新增编辑必填校验](./2026-06-17_task-form-required-validation.md)（定时日期/开始时间必填校验，本次仍保留）

## 记录日期

2026-06-30
