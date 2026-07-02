---
name: frontend-crud-error-success-toast
description: 修复前端保存/新增/删除时接口异常后仍弹成功提示的问题
metadata:
  type: project
---

## 需求描述

用户反馈：保存、新增、删除等操作在接口抛出异常并弹出错误弹窗后，仍然会弹出成功弹窗。

## 状态

已完成

## 涉及范围

### 前端

- `src/views/manage/user/modules/user-operate-drawer.vue`
- `src/views/scene/map/modules/scene-map-detail-drawer.vue`

## 约束与备注

- 项目 HTTP 请求统一走 `@sa/axios` 的 `createFlatRequest`，失败时返回 `{ data: null, error }` 而不是抛出异常；全局 `onError` 钩子会自动弹出错误提示。
- 因此业务组件中不能依赖 `try...catch` 拦截请求失败，而应在调用后检查 `error` 字段，仅在 `!error` 时才执行成功提示、关闭抽屉、刷新列表等后续动作。
- 已排查全库 `await fetchXxx(); window.$message?.success(...)` 模式，上述两处为遗漏点；其余 CRUD 组件已正确使用 `const { error } = await ...` 判断。

## 相关文件

- `frontend/src/views/manage/user/modules/user-operate-drawer.vue`
- `frontend/src/views/scene/map/modules/scene-map-detail-drawer.vue`
- `frontend/src/service/request/index.ts`
- `frontend/packages/axios/src/index.ts`

## 记录日期

2026-07-02
