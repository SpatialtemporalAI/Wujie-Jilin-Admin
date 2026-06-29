# 菜单管理：路径前缀继承、目录级联、移到根目录修复

## 需求描述

菜单管理对路由 `path`（路径前缀）的维护存在三个问题，本次一并修复：

1. **目录编辑支持修改并级联**：编辑目录时可改其路径，且需同步更新所有子菜单的路径前缀（此前 `routePath` 字段恒禁用，子菜单 path 不会跟随）。
2. **菜单路径前缀锁定 + 新增自动拼接**：编辑有父级目录的菜单时，父级传过来的路径前缀不可改（只读），仅可编辑自身段；新增菜单保存时自动取上级目录（存在且非根）的路径前缀进行拼接。
3. **移到根目录可正常显示**：此前把菜单从目录移到根目录后无法访问——移到根目录后 `component` 仍是 `view.xxx`（无 layout），且 SoybeanAdmin 会丢弃「路由名含 `_` 的根路由」。

## 状态

已完成

## 涉及范围

### 后端

- [backend/modules/admin/schemas/sys/menu.py](../../../backend/modules/admin/schemas/sys/menu.py)：`SysMenuTreeResponse` 新增 `routePath`（Optional，alias `path`），供前端查父级路径前缀。
- [backend/modules/admin/services/sys/menu_service.py](../../../backend/modules/admin/services/sys/menu_service.py)：
  - `get_menu_tree` 构造响应时带 `routePath=menu.path`。
  - 新增模块函数 `_normalize_menu_component(component, has_parent)`：含 `view.` 的组件按挂载层级规范化——根路由 → `layout.<layout>$view.<page>`、嵌套 → `view.<page>`；保留用户选的 layout 名（如 blank），缺省 base。目录/外链/按钮原样返回。
  - 新增静态方法 `_collect_descendant_ids(db, menu_id)`：一次性加载 (id,parent_id) 按层遍历收集全部后代。
  - `update_menu`：记录 `old_path`；应用更新后若 `path` 变更，对所有后代做**前缀替换**（`child.path.startswith(old+"/")` → 用 `new` 替换前缀段，单次替换即覆盖任意深度；仅改 `path`，不动 `name`/`component`）；最后对 `type==MENU` 规范化 `component`。

### 前端

- [frontend/src/views/manage/menu/modules/shared.ts](../../../frontend/src/views/manage/menu/modules/shared.ts)：新增 `getLastSegmentByName`（按 `_` 取末段）、`getLastPathSegment`（按 `/` 取末段）、`composePath(prefix, segment)`（归一拼接，`/manage`+`face`→`/manage/face`，`""`+`monitor`→`/monitor`）。
- [frontend/src/typings/api/system-manage.d.ts](../../../frontend/src/typings/api/system-manage.d.ts)：`MenuTree` 增 `routePath?: string`。
- [frontend/src/views/manage/menu/modules/menu-operate-modal.vue](../../../frontend/src/views/manage/menu/modules/menu-operate-modal.vue)：
  - model 用 `pathSegment`（可编辑）替换原禁用的 `routePath`；新增计算属性 `menuPathMap`（扁平 id→routePath）与 `pathPrefix`（父级目录完整路径，只读；无父级为空）。
  - 路径输入改为 `NInputGroup`：只读前缀框 + 可编辑自身段；目录（menuType=1）同样可编辑自身段。
  - 打开时先 `await getMenuTree()` 再 `handleInitModel()`，确保父级前缀可查；edit 时按「父级前缀」拆出 `pathSegment`。
  - `menuName` watcher：新增菜单时按名末段自动填 `pathSegment`（edit 不覆盖）。
  - `parentId` watcher：移到根目录且路由名含 `_` 时自动裁成末段（所见即所得）。
  - `getSubmitParams`：`routePath = composePath(pathPrefix, pathSegment)`；根路由且名含 `_` 时提交名裁末段；`component` 按 `willBeRoot` 取 `layout.base$view.<page>` 或 `view.<page>`（修复 layout 丢失）。

## 关键决策

- **`path` 与 `name` 解耦**：SoybeanAdmin 的视图按**完整路由名**在构建期映射（`router/elegant/imports.ts`：`manage_face → views/manage/face/index.vue`），`transform.ts` 又以路由名是否含 `_` 判定一级/嵌套。故 `name`/`component` 必须继续引用既有视图 key，**目录改名只改 `path`（URL）**，不做 name 重命名，避免视图丢失。
- **需求3「移到根目录」策略（用户选定）= 自动转为根路由**：移到根目录时把路由名裁成末段（`manage_face → face`，根路由名不能含 `_`），路径改 `/face`，组件改 `layout.base$view.manage_face`（`page` 仍用原视图 key 保证解析），使其作为一级路由渲染原页面。代价：路由名/i18n key 会变，侧边栏文案可能需补 `route.face` 翻译。
- **后端 component 规范化作安全网**：即使前端疏漏也能避免「移到根目录后 `view.xxx` 无 layout」导致路由被丢弃、页面无法访问；幂等（已正确时原样返回）。
- **已知限制（本次不处理）**：把根级菜单（视图 key 不含 `_`，如 `monitor`）移**进**目录是对称的框架限制（嵌套路由名须含 `_`），不在本次范围。

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]）：本次改动文件**零新增类型错误**；仓库中 `src/views/scene/map/**` 等为预存报错，与本次无关。
- 后端 `py_compile` 通过；逻辑覆盖场景：目录改路径级联子菜单、新增子菜单自动拼前缀、编辑菜单前缀锁定、`manage_face` 移到根目录、不含 `_` 菜单移到根目录。

## 相关文件

- `backend/modules/admin/schemas/sys/menu.py`（`SysMenuTreeResponse` 加 `routePath`）
- `backend/modules/admin/services/sys/menu_service.py`（`get_menu_tree` 带 routePath；`update_menu` 级联 + 规范化；新增 `_normalize_menu_component` / `_collect_descendant_ids`）
- `frontend/src/views/manage/menu/modules/shared.ts`（3 个工具函数）
- `frontend/src/views/manage/menu/modules/menu-operate-modal.vue`（前缀/段拆分、watcher、提交重算）
- `frontend/src/typings/api/system-manage.d.ts`（`MenuTree.routePath`）

## 记录日期

2026-06-29
