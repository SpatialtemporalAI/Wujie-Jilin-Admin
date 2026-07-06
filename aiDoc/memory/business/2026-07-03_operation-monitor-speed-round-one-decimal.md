# 运行监控：机器人行走速度按小数点后一位判断是否移动

**日期**: 2026-07-03
**提出者**: 用户

## 需求描述

运行监控页（operation-monitor）机器人状态卡片「速度」一栏的「移动中 / 静止」判断：行走速度只保留小数点后一位进行判断，保留一位小数后不为 0 则判为行走中（移动中），否则为静止。

## 状态

已完成

## 涉及范围

### 后端

无改动（纯前端）。

### 前端

仅改 `frontend/src/views/operation-monitor/modules/robot-status-card.vue` 的 `getSpeedLabel()`：判断前先把 speed 保留一位小数（`Math.round(speed * 10) / 10`），再 `> 0` 判为「移动中」，否则「静止」。

## 约束与备注

- **根因**：原判断为直接 `speed > 0`，而速度显示值已用 `toFixed(1)` 保留一位小数（模板第 147 行 `statusRecord?.speed?.toFixed(1)`）。传感器存在微小波动（如 0.04 m/s），按原始值 `> 0` 会误判为「移动中」，与显示的 `0.0` 矛盾。
- **判断与显示对齐**：保留一位小数后再判断，使「移动中/静止」结论与画布显示的速度数值一致：显示 `0.0` 即静止，显示 `0.1` 及以上即移动中。
- **实现方式**：用 `Math.round(speed * 10) / 10` 而非 `Number(speed.toFixed(1))`，避免字符串往返；两者对正数等价（均四舍五入）。
- **边界**：speed 为 undefined/null 时 `Math.round(undefined * 10)` → `NaN > 0` 为 false，返回「静止」，与原 `speed > 0` 行为一致；模板外层已 `v-if="statusRecord"` 守卫。
- 文案保持「移动中 / 静止」不变（用户所述「行走中」为状态语义描述，非文案变更要求）。
- 验证：`pnpm typecheck`（本次改动不触发新类型错误；存量 i18n `map-editor` 路由 key 报错与本次无关）。

## 相关文件

- `frontend/src/views/operation-monitor/modules/robot-status-card.vue`（`getSpeedLabel`、速度显示 `toFixed(1)`）

## 相关历史记忆

- [2026-07-02 运行监控未绑定场景地图时不显示机器人点位](./2026-07-02_operation-monitor-hide-robot-point-without-map.md)（同属 operation-monitor 状态卡片/地图相关调整）

## 记录日期

2026-07-03
