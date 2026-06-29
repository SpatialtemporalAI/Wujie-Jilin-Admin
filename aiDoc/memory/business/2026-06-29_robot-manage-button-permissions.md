# 机器人管理卡片按钮补齐权限控制

## 需求描述

机器人管理页（卡片式列表）的操作按钮缺少权限控制，除「新增」外，卡片底部的编辑 / gRPC配置 / 状态 / 删除按钮对所有人可见，未按权限码隐藏。

## 状态

已完成

## 涉及范围

- `frontend/src/views/robot/manage/index.vue`：卡片底部 4 个按钮逐个加 `v-if="hasAuth(...)"`，对齐同文件「新增」按钮已有的写法与 `robot/model/index.vue` 的做法

### 权限码映射

| 按钮 | 权限码 | 说明 |
| --- | --- | --- |
| 新增 | `robot:manage:add` | 改动前已存在，未动 |
| 编辑 | `robot:manage:edit` | 本次新增 |
| gRPC配置 | `robot:manage:grpc_config` | 本次新增 |
| 状态 | `robot:manage:list` | 本次新增 |
| 删除 | `robot:manage:delete` | 本次新增（含 `NPopconfirm` 整体加 `v-if`） |

## 关键决策

- **写法**：直接用 `v-if="hasAuth('<code>')"`，与该文件第 117 行新增按钮、`robot/model/index.vue` 表格列 `hasAuth(...) && (...)` 保持同一套 `useAuth` 体系，未引入 `v-permission` 指令
- **状态按钮权限码**：后端无独立 `robot:manage:status` 权限点，状态查看属读操作，复用 `robot:manage:list`（后端 `robot_status_record` 接口即用 list 权限）
- **状态按钮历史**：该按钮在 [[2026-06-24_robot-manage-grpc-config-and-fixes]] 中曾被隐藏（移除 `hasAuth('robot:manage:list')` 那段），当前代码已恢复显示，本次顺带给它补回 list 权限
- **未动后端**：所有权限码均为既有菜单按钮权限，无新增权限点、无 DDL

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），未做 UI 测试
- typecheck 通过；本次改动文件无新增类型错误（仓库中 `src/views/scene/map/**` 的类型报错为预存问题，与本次无关）

## 记录日期

2026-06-29
