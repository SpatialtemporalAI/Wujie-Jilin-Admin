# 菜单管理本地图标类型不生效

## 需求描述

菜单管理-新增/编辑菜单时，图标类型选择「本地」（iconType="2"）并选择了一个
本地 svg 后保存，列表 / 表单回显时 iconType 永远回到默认「iconify」（"1"），
本地图标渲染不出来。

## 根因

全栈从数据库到前端从未持久化 iconType 字段：

| 层 | 现状 |
|---|---|
| 数据库 `sys_menu` | 只有 `meta_icon` 列，没有 icon_type 类列 |
| ORM `SysMenu` | 只有 `meta_icon` 字段 |
| `SysMenuCreate` / `SysMenuUpdate` schema | 不接收 iconType 入参 |
| `SysMenuResponseData` schema | `iconType` 字段写死默认 `"1"`，没从任何列读 |
| `fetchCreateMenu` / `fetchUpdateMenu` | data payload 不传 `meta_icon_type` |

前端表单的 `model.iconType` 虽然在 UI 上能选，但：
- 保存时根本没发给后端
- 即使发了，后端也没字段接
- 回显时永远是默认 "1"

## 状态

已完成

## 涉及范围

### 数据库

- `backend/database/alembic/versions/0031_menu_meta_icon_type.py`
  - 新建迁移：`ALTER TABLE sys_menu ADD COLUMN meta_icon_type VARCHAR(2) NOT NULL DEFAULT '1'`
  - 注：直接 add column（小列加默认），不新建并存表（符合小改不双表的惯例）
  - down_revision = `0030_robot_grpc_config`

### 后端

- `backend/database/models/sys/menu.py`
  - 新增 `meta_icon_type: Mapped[str] = mapped_column(String(2), nullable=False, default="1", server_default="1", ...)`

- `backend/modules/admin/schemas/sys/menu.py`
  - `SysMenuCreate` 新增 `meta_icon_type: str = Field("1", ...)`
  - `SysMenuUpdate` 新增 `meta_icon_type: Optional[str] = Field(None, ...)`
  - `SysMenuResponseData.iconType` 从写死 `"1"` 改为
    `validation_alias=AliasChoices("meta_icon_type", "iconType")`，从 ORM 字段读取

- `backend/modules/admin/services/sys/menu_service.py`
  - `create_menu` 显式传 `meta_icon_type=menu_create.meta_icon_type`
  - `update_menu` 用 `model_dump(exclude_unset=True)` + `setattr` 循环，
    ORM 已有 `meta_icon_type` 属性，自动生效，无需改

### 前端

- `frontend/src/service/api/system-manage.ts`
  - `fetchCreateMenu` data 增加 `meta_icon_type: menu.iconType || '1'`
  - `fetchUpdateMenu` data 增加 `meta_icon_type: menu.iconType || '1'`
  - 前端表单 `model.iconType` 已存在（[menu-operate-modal.vue:151](frontend/src/views/manage/menu/modules/menu-operate-modal.vue#L151)），无需改

### 左侧菜单渲染链路（同样需要透传 localIcon）

- `backend/modules/admin/schemas/sys/route.py`
  - `RouteMetaResponse` 新增 `localIcon: str | None` 字段
- `backend/modules/admin/services/sys/route_service.py`
  - `_menu_to_route` 根据 `menu.meta_icon_type` 分流：
    - `"2"` → 填 `localIcon=menu.meta_icon`，`icon=None`
    - 其他 → 填 `icon=menu.meta_icon`，`localIcon=None`
  - 前端 `store/modules/route/shared.ts` 已从 `route.meta.localIcon` 读取并交给 SvgIcon，
    `localIcon` 存在时优先渲染本地图标（[svg-icon.vue:40](frontend/src/components/custom/svg-icon.vue#L40)）

## 关键决策

### 字段名：`meta_icon_type`

- 与已有 `meta_icon` / `meta_hidden` / `meta_keep_alive` 等 meta_* 前缀一致
- 体现「路由元信息」语义，便于和后端路由生成层对齐
- 响应 schema 用 `AliasChoices("meta_icon_type", "iconType")` 同时兼容 snake_case 列名与前端驼峰

### 字段类型：VARCHAR(2) + server_default

- 只有两个枚举值 "1"/"2"，VARCHAR(2) 足够
- `server_default="1"` 保证旧数据迁移后默认值是 iconify（与原行为一致）
- `nullable=False` 避免脏数据

### 不引入 enum 列

- 用 VARCHAR(2) 而非 ENUM，避免 PG/MySQL 在 ENUM 上的差异
- 项目其他字段也大量使用字符串枚举（如 grpc_retry_task.status），保持一致

### 保留前端图标类型单选交互

- `menu-operate-modal.vue` 的 `iconType` 单选 + 本地图标下拉的 UI 不变
- `index.vue` 列表渲染 `row.iconType === '1' ? row.icon : undefined` 不变
- 只补全持久化链路

## 验证方案

### 场景 1：本地图标保存生效

- 进入菜单管理 → 新增菜单（或编辑已有菜单）
- 图标类型选择「本地」
- 在本地图标下拉中选择一个 svg（如 `mdi:account` 实际是 `/src/assets/svg-icon/mdi-account.svg`）
- 保存 → 列表 icon 列应渲染出本地图标
- 编辑同一条 → iconType 仍是「本地」，下拉仍选中之前的图标

### 场景 2：iconify 图标不受影响

- 图标类型选择「iconify」
- 在 input 中填入 `mdi:account`
- 保存 → 列表渲染 iconify 图标
- 编辑同一条 → iconType 仍是「iconify」

### 场景 3：旧数据迁移

- 已有菜单 meta_icon_type 默认为 "1"（iconify）
- 旧菜单渲染行为与修复前一致

### 静态检查

- `python -m py_compile` 通过（schema / service / model / migration）
- 前端 `pnpm typecheck`：本次改动的文件未引入新 TS 错误
  （其余 scene/map 报错为项目原有问题，与本次无关）

## 部署注意

- 部署时执行 `alembic upgrade head` 应用 0031 迁移
- 迁移为加列 + server_default，PG/MySQL 均可在不停服情况下完成
- 旧菜单数据自动获得 `meta_icon_type='1'`，行为与修复前一致

## 相关文件

后端：
- `backend/database/alembic/versions/0031_menu_meta_icon_type.py`
- `backend/database/models/sys/menu.py`
- `backend/modules/admin/schemas/sys/menu.py`
- `backend/modules/admin/services/sys/menu_service.py`
- `backend/modules/admin/schemas/sys/route.py`
- `backend/modules/admin/services/sys/route_service.py`

前端：
- `frontend/src/service/api/system-manage.ts`

## 记录日期

2026-06-26
