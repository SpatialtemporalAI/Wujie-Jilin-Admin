# 任务管理选地图权限 + gRPC 重试任务去重

## 需求描述

两个独立修复：

### 1. 任务管理新增任务时选择地图列表 403

任务管理-任务列表，新增任务时点击「场景地图」下拉，前端调用 `GET /scene/map/list`，
该接口当前权限是 `require_any_permission("scene:map:list", "scene:map-editor:list")`，
只有任务模块权限（`task:list`）的用户被挡，axios 拦截器冒出红色提示「没有操作权限: scene:map:list」。

注：2026-06-24 任务 5 曾用「前端懒加载 + 容错」修过编辑场景（见
[[2026-06-24_robot-manage-grpc-config-and-fixes]]），但只避免抽屉卡死，
axios 拦截器在响应层依然抛 message.error；本次切换到「后端权限 OR」根治。

### 2. gRPC 推送失败重试的同业务键去重

参数配置发送失败入队时不去重。典型问题场景：

> 对同一条 face 记录「先编辑后删除」，UPDATE 推送失败入队后，
> DELETE 又入队——重试时设备端会先收到 UPDATE（把已删除的人脸又同步过去），
> 再收到 DELETE（删除）。中间产生短时不一致，且浪费一次推送。

需求：同 id 同配置去重；同 face 的连续操作，新操作覆盖旧操作。

## 状态

已完成

## 涉及范围

### Q1：scene_map list 接口权限 OR 加入 task:list

- `backend/modules/scene/endpoints/scene_map.py`
  - `GET /scene/map/list` 权限从 `(scene:map:list, scene:map-editor:list)` 扩展为
    `(scene:map:list, scene:map-editor:list, task:list)`
  - 任务管理用户靠已有的 `task:list` 通过，无需新增菜单权限点
  - 不放宽 detail / add / edit / delete 等其他 scene_map 端点（最小授权）

### Q2：gRPC 重试任务按业务键去重

- `backend/modules/grpc/retry_service.py`
  - import 增加 `update`
  - 模块级新增 `_superseded_clause(service_name, method_name, payload)`：
    构造「同业务键的 pending 任务」WHERE 条件列表
    - `face_recognition` → 用 `payload->>'face_id'` 匹配（PG JSON 路径，
      SQLAlchemy 操作符 `GrpcRetryTask.payload["face_id"].as_string()`）
    - voice / speed / battery → 用 `robot_id` 列匹配（已有字段）
  - `GrpcRetryService` 新增 `_cancel_superseded(db, *, service_name, method_name, payload)`：
    UPDATE 旧 pending 任务为 `status='cancelled' / last_error='被新操作覆盖，不再重试'`
  - `save_pending` 入口先调 `_cancel_superseded`，再 INSERT 新任务
- `backend/database/models/business/grpc_retry_task.py`
  - 模块 docstring 补一行说明 cancelled 语义
  - `status` 列 comment 从 `pending/completed/dead` 扩展为 `pending/completed/dead/cancelled`
  - **无 DDL**：`status` 本就是 `String(16)`，新值是字符串，无需迁移

## 关键决策

### Q1：复用 task:list，不新增独立权限

- 与 [[2026-06-25_param-config-grpc-from-robot]] 中"复用 scene:map-editor:edit"思路一致，
  避免菜单 / 权限点膨胀
- `task:list` 是任务模块最低门槛权限，能进任务页面的用户都有，覆盖典型场景
- 不放宽 scene_map 其他写接口（detail/add/edit/delete），避免越权

### Q2：业务键规则按服务特性分别定义

| Service | 业务键 | 取消规则 |
|---|---|---|
| face_recognition | `payload.face_id` | 同 face 的 CREATE/UPDATE/DELETE 互斥，新操作覆盖旧操作 |
| voice / NotifyWakeWordChanged | `robot_id` | 同 robot 的唤醒词最终值覆盖中间值 |
| voice / NotifyTTSConfigChanged | `robot_id` | 同 robot 的 TTS 最终值覆盖中间值 |
| speed / NotifySpeedLevelChanged | `robot_id` | 同 robot 速度等级最终值覆盖 |
| battery / NotifyBatteryThresholdChanged | `robot_id` | 同 robot 电量阈值最终值覆盖 |

### Q2： cancelled 状态而非 dead

- `dead` 语义是「重试上限失败」，是被动的错误终态
- `cancelled` 语义是「被新操作覆盖」，是主动的合理终态
- 两者都是终态（不再被 `run_pending_once` 扫描），但便于审计区分
- 重试扫描条件 `status == "pending"` 自然跳过 cancelled，无需改扫描逻辑

### Q2：跨数据库兼容性

- 用 SQLAlchemy 的 `Column["key"].as_string()` 而非原生 SQL `payload->>'face_id'`
- 项目主用 PostgreSQL，但 `database/config.py` 也支持 MySQL；JSON 路径操作符由 SQLAlchemy 翻译

## 约束与备注

- 前端无改动（沿用 2026-06-24 的懒加载 + 占位 option 容错）
- 测试类 RPC（TestWakeWord / TestTTSConfig）不入重试表，本就不受影响
- 已 completed / dead 的任务不被取消（只针对 pending）
- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），本次纯后端无 typecheck

## 验证方案

### Q1

- 仅 `task:list` 权限的用户 → 进入任务管理 → 新增任务 → 点击场景地图下拉
  - 期望：下拉正常显示地图列表，无 403 提示
- 仅 `scene:map:list` 权限的用户 → 行为不变

### Q2

档 1：face「先编辑后删除」
- 编辑 face_id=5 推送失败 → 入队 UPDATE face_id=5
- 立刻删除 face_id=5 推送失败 → 旧 UPDATE 被取消（status=cancelled），新 DELETE 入队
- 设备上线后，重试只发一次 DELETE

档 2：voice 连续两次保存
- 第一次保存（开关=true）失败 → 入队 wake_word_enabled=true
- 第二次保存（开关=false）失败 → 旧任务被取消，新任务 wake_word_enabled=false 入队
- 重试只发一次，值为 false

档 3：保留 face CREATE 后未掉线场景
- CREATE face_id=5 推送成功 → 任务不入队
- DELETE face_id=5 推送失败 → 入队 DELETE，无旧任务可取消（正常路径）

### 静态检查

- `py_compile` 通过
- 导入检查：`from modules.grpc.retry_service import GrpcRetryService, _superseded_clause`

## 相关文件

后端：
- `backend/modules/scene/endpoints/scene_map.py`
- `backend/modules/grpc/retry_service.py`
- `backend/database/models/business/grpc_retry_task.py`

## 记录日期

2026-06-26
