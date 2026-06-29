# 菜单管理按钮权限补全 i18n

## 需求描述

菜单管理页表格里所有「按钮」类型（menuType=3）的权限节点，名称列残缺显示成 `route.xxx`（如 `route.manage_menu_add`、`route.新增任务`）。

根因：后端 `SysMenuResponseData.set_auto_fields`（[backend/modules/admin/schemas/sys/menu.py](../../../backend/modules/admin/schemas/sys/menu.py)）对所有菜单（含按钮）在 `i18nKey is None` 时自动生成 `i18nKey = route.{name}`；但按钮的 `name`（如 `manage_menu_add`）在 locale 的 `route` 段没有对应翻译，`fallbackLocale: 'en'` 也找不到，于是 `$t(i18nKey)` 回退成 key 本身。前端 [frontend/src/views/manage/menu/index.vue](../../../frontend/src/views/manage/menu/index.vue) 的 menuName 列 `i18nKey ? $t(i18nKey) : menuName` 因此对按钮恒走 `$t` 分支，显示残缺。

## 状态

已完成

## 涉及范围

### 后端

- 新增迁移 [backend/database/alembic/versions/0035_rename_scheduler_buttons.py](../../../backend/database/alembic/versions/0035_rename_scheduler_buttons.py)：把 8 个用中文作 name 的 scheduler 按钮改成 ASCII 键名（与全仓 `manage_menu_add` 等命名一致）。**仅改 `name` 字段**，`permission` 权限码、`sys_role_menu` 角色绑定（按 menu id 关联）均不变。
- 同步更新 [backend/database/alembic/versions/0002_seed_data.py](../../../backend/database/alembic/versions/0002_seed_data.py) 中对应 8 条种子，保证全新安装的库一致。

#### scheduler 按钮 8 条重命名映射

| 旧 name（中文） | 新 name（ASCII） | 权限码（不变） |
| --- | --- | --- |
| 新增任务 | manage_scheduler_add | sys:scheduler:add |
| 编辑任务 | manage_scheduler_edit | sys:scheduler:edit |
| 删除任务 | manage_scheduler_delete | sys:scheduler:delete |
| 任务详情 | manage_scheduler_detail | sys:scheduler:detail |
| 启停任务 | manage_scheduler_status | sys:scheduler:status |
| 手动执行 | manage_scheduler_trigger | sys:scheduler:trigger |
| 日志详情 | manage_scheduler-log_detail | sys:scheduler:log:detail |
| 删除日志 | manage_scheduler-log_delete | sys:scheduler:log:delete |

### 前端

- [frontend/src/locales/langs/zh-cn.ts](../../../frontend/src/locales/langs/zh-cn.ts) 与 [frontend/src/locales/langs/en-us.ts](../../../frontend/src/locales/langs/en-us.ts) 的 `route` 段补全 **全部约 63 个按钮权限**的中英文翻译，文案统一用**动作词**（查询/新增/编辑/删除/上传/下载/发布/移除/下线/查看/详情/启停/手动执行/启动/暂停·恢复/gRPC配置）——按钮作为树子节点挂在父菜单下，模块上下文由父菜单提供。

## 关键决策

- **实现方式（用户选定）**：前端补全翻译 + 新迁移重命名 8 个中文按钮，而非「仅前端补全（接受中文 key）」或「仅渲染兜底」。理由：与全仓 ASCII 命名风格统一，避免 locale 里混入 `route.新增任务` 这类非法形态 key。
- **文案风格（用户选定）**：动作词，非「模块+动作」。
- **按钮翻译放在 `route` 命名空间**：渲染逻辑 `$t(i18nKey)` 且 i18nKey 恒为 `route.{name}`，故必须落在 `route` 下才能命中；未引入独立 `button` 命名空间（那需扩展 `App.I18n.Schema` 类型 + 改后端 i18nKey 前缀，改动过大）。
- **类型说明**：`route` 段类型为 `Record<I18nRouteKey, string>`，`I18nRouteKey` 派生自 elegant-router 按视图生成的 `RouteMap`（不含按钮键）。实测新增按钮键**不产生 TS 错误**（与预存的 `loginSpace` 多余键同理，本项目对 route 段多余键本就容忍，typecheck 早已非零退出）；运行时 `$t` 直接从 messages 取值，与 TS 类型无关，可正常解析。

## 按钮权限来源盘点

按钮节点跨多个迁移播种：0002（系统/日志/文件/scheduler）、0003（robot_model/robot_manage/scene_group/scene_map）、0005（task）、0011（operation_monitor_list）、0024（scene_map_editor）、0027（task_execution_start/control）、0030（robot_manage_grpc_config）、0034（merchant_list/add/edit/delete）。本次翻译覆盖以上全部。

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），未做 UI 测试。
- typecheck 通过：本次改动文件**零新增类型错误**；仓库中 `src/views/scene/map/**`、`src/hooks/business/dict.ts`、locale 的 `loginSpace` 为预存报错，与本次无关。

## 相关文件

- `backend/database/alembic/versions/0035_rename_scheduler_buttons.py`（新增）
- `backend/database/alembic/versions/0002_seed_data.py`（改 8 条 name）
- `frontend/src/locales/langs/zh-cn.ts`、`frontend/src/locales/langs/en-us.ts`（route 段补全）
- 渲染入口：`frontend/src/views/manage/menu/index.vue`（menuName 列）

## 记录日期

2026-06-29
