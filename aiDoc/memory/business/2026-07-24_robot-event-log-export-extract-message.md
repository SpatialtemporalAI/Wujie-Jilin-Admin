# 机器人事件日志：导出「事件内容」从 JSON 提取 message

## 需求描述

机器人事件日志列表导出的 Excel，「事件内容」列原样输出 `event_content` 字段（JSON 字符串），用户希望与列表展示一致——只输出 JSON 里的 `message` 文本。

## 背景

- `event_content` 以 JSON 字符串存储（如 `{"message": "...", ...}`）。
- 前端列表早已用 `frontend/src/utils/robot-event.ts` 的 `parseEventContentMessage` 展示：JSON 解析成功且 `message` 为非空字符串则返回 `message`，否则（非 JSON / 解析失败 / 缺 message）回退原始内容。
- 后端导出配置 `backend/modules/admin/exports/robot_event_log_export.py` 的 `event_content` 列此前无 `transform`，直接把 JSON 原文写进单元格，与列表展示不一致。

## 关键实现

- `backend/modules/admin/exports/robot_event_log_export.py`：
  - 新增 `import json` 与模块级函数 `_extract_event_message(value)`，逻辑与前端 `parseEventContentMessage` 完全对齐：
    - 空值 → `""`
    - `json.loads` 失败 / 非 dict / `message` 非字符串或为空 → 回退原始内容
    - `message` 为非空字符串 → 返回 `message`
  - `event_content` 列绑定 `transform=_extract_event_message`。
- 仅改导出取值逻辑，不动列顺序、列名、查询、`enrich_fn`，不影响接口契约。

## 约束与备注

- 与前端单点对齐：导出单元格内容 == 列表 `parseEventContentMessage` 输出，非 JSON / 无 message 不会丢内容（回退原文）。
- 不需要 DB 迁移、不改 schema、不改通用导出框架。
- 后端改动需重启 FastAPI 生效。
- 通用导出取值 `_get_value` 在 `val is None` 时不调 `transform`（直接返回空串），故 transform 内的 `if not value` 兜底主要防御空串/假值。

## 验证

`_extract_event_message` 用 9 个用例对齐前端语义全部通过：JSON 含 message、JSON 无 message、非法 JSON、None、空串、message 为空串、message 非字符串（123）、纯文本、message 含双引号。

## 相关文件

- 后端：`backend/modules/admin/exports/robot_event_log_export.py`
- 前端（对齐基准，未改动）：`frontend/src/utils/robot-event.ts`、`frontend/src/views/log/robot-log/index.vue`

## 记录日期

2026-07-24
