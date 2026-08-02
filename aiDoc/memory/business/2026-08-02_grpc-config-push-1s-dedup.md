# 机器人配置类 gRPC 推送 1s 内重复 —— 前后端双重防重

## 需求描述

后端是 gRPC 客户端，把语音/速度/电量等配置下发给机器人。线上观察到「同一配置在 1s 内被重复推送两次」，机器人收到冗余消息。要求排查根因，并在前后端都加防重。

## 根因

- 后端实时推送本身没有任何去重门：`cancel_superseded`（modules/grpc/retry_service.py）只取消旧的「待重试任务」，不拦截实时 RPC；4 个配置推送调用点（voice×2 / speed / battery）都汇入 `_push_with_retry`（modules/robot/services/robot_config_service.py），每次进来都发 RPC。
- 前端三个保存按钮存在双击竞态：voice-synthesis-tab 的 `saving` 标志设在 `await validate()` 之后（最严重），walking-speed / battery-threshold 顶部缺 `if (saving.value) return` guard。

## 状态

已完成

## 方案（前后端都加）

### 后端：进程内 TTL 去重门（兜底）

- 新增 `backend/modules/grpc/push_dedup.py`：键 = `(service_name, method_name, robot_id, payload_hash)`，窗口默认 1.0s；只压「字节级完全相同」的重复（不同值如速度 low→high 照常下发）；「预约式」置位（check+set 间无 await，asyncio 单线程原子，挡并发相同请求）；用 `time.monotonic()` + dict 机会式过期清理。
- 在 `_push_with_retry` 的 `ENABLED` 短路之后、`cancel_superseded` 之前接入：命中即记 `grpc push suppressed(dedup ...)` 日志并返回 `"synced"`。
- 已知边界（可接受）：上一次若因离线/失败走了 save_pending（设备尚未真正收到），本次重复被压下会回 `"synced"`，但重试队列仍兜底投递，最终一致；需「1s 内重复 + 离线/失败」同时成立。

### 前端：保存按钮顶层互斥锁（源头）

三个 handler 统一改成「`if (saving.value) return` → 立即 `saving.value = true` → try/finally 释放」，锁必须在任何 await（含 validate）前置位：

- voice-synthesis-tab.vue `handleSaveVoice`（`saving=true` 原在 `await validate()` 之后，已上移）
- walking-speed-tab.vue `handleSave`（补顶层 guard + 锁上移到机器人校验之前）
- battery-threshold-tab.vue `handleSave`（同上）

不引入新 composable，沿用各组件已有 `saving` ref + `:loading="saving"` 模式。

## 涉及范围

### 后端

- 新增 `backend/modules/grpc/push_dedup.py`
- 改 `backend/modules/robot/services/robot_config_service.py`（`_push_with_retry` 接入去重门 + import）

### 前端

- 改 `frontend/src/views/settings/modules/voice-synthesis-tab.vue`
- 改 `frontend/src/views/settings/modules/walking-speed-tab.vue`
- 改 `frontend/src/views/settings/modules/battery-threshold-tab.vue`

## 约束与备注

- 范围限定机器人配置（语音/速度/电量）一类。
- 地图保存 NotifyMapSaved、任务广播 broadcast_task_changed、切换地图 SwitchMap 同样没有实时去重门，结构类似，后续可复用 `push_dedup.py` 推广，本次不做。
- 后端去重仅进程内、单 worker 足够；多 worker 下同进程重复仍能挡住，跨进程重复由前端互斥锁 + 重试队列 cancel_superseded 兜底。

## 相关文件

- `backend/modules/grpc/push_dedup.py`
- `backend/modules/robot/services/robot_config_service.py`
- `backend/modules/grpc/retry_service.py`（cancel_superseded，参考）
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`
- `frontend/src/views/settings/modules/walking-speed-tab.vue`
- `frontend/src/views/settings/modules/battery-threshold-tab.vue`

## 记录日期

2026-08-02
