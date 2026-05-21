# 前端开发规范

## 基础规则

- HTTP 请求统一走 `@sa/axios` 封装（`packages/axios/`），通过 `src/service/request/` 调用
- 全局状态使用 Pinia（`src/store/`），禁止在组件中直接操作全局变量
- 路由必须配置完整元数据（权限、标题、图标），使用项目内置异步路由机制
- 所有变量、函数参数、返回值必须有明确的 TypeScript 类型声明

## 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 文件名 | `kebab-case` | `system-manage.ts`、`user-detail.vue` |
| 组件名 | `PascalCase` | `UserTable`、`RoleForm` |
| 变量名 | `camelCase` | `userInfo`、`currentPage` |
| 常量名 | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| API 函数 | `fetch` 前缀 | `fetchGetUserList`、`fetchCreateUser` |
| 类型名 | `PascalCase` | `UserInfo`、`PageParams` |

## TypeScript 要求

- API 响应类型定义在 `src/typings/api/<domain>.d.ts`，放在 `Api` 命名空间下
- 公共类型（分页、状态等）定义在 `src/typings/api/common.d.ts`
- i18n 类型约束在 `src/typings/app.d.ts` 的 `App.I18n.Schema`
- 修改数据结构时必须同步更新对应类型声明
- 提交前执行 `pnpm typecheck` 确保类型安全

## 组件规范

- 公共组件放在 `src/components/`
- 页面级组件放在对应页面的 `modules/` 目录
- Props 必须使用 TypeScript 接口定义（`defineProps<{ ... }>()`）
- 每个页面必须有独立文件夹，包含主 `.vue` 文件
- 相关子组件放在 `modules/` 子目录

### 搜索表单标准模式

列表页的搜索表单统一使用以下 NaiveUI 组件组合：

- `NCard` 包裹，`size="small"` `class="card-wrapper"`
- `NCollapse` + `NCollapseItem` 折叠容器，标题使用 `$t('common.search')`
- `NForm label-placement="left" :label-width="80"` 左对齐标签
- `NGrid responsive="screen" item-responsive` 响应式网格
- `NFormItemGi span="24 s:12 m:6" class="pr-24px"` 表单项，小屏 2 列、中屏 4 列
- 按钮行 `NFormItemGi span="24 m:12"`，`NSpace justify="end"` 右对齐
- 重置按钮：`icon-ic-round-refresh` 图标
- 搜索按钮：`icon-ic-round-search` 图标，`type="primary" ghost`
- 重置逻辑使用 `jsonClone(toRaw(model.value))` + `Object.assign`

参考实现：`src/views/manage/config/modules/config-search.vue`

## 页面规范

新增页面时必须完成：

1. 在 `src/views/<name>/` 创建文件夹和 `.vue` 文件
2. 在 `src/locales/langs/zh-cn.ts` 和 `en-us.ts` 添加翻译
3. 在 `src/typings/app.d.ts` 更新 `App.I18n.Schema` 类型
4. 运行 `pnpm gen-route` 自动生成路由

## 样式规范

- 样式优先级：UnoCSS > SCSS > 内联样式（避免使用内联样式）
- 遵循 NaiveUI 的设计模式，保持视觉一致性
- 主题控制通过 CSS 变量实现
- 全局样式放在 `src/styles/`

## 国际化规范

- 所有用户可见文本必须通过 i18n 键引用
- 新增键必须同时添加到 `zh-cn.ts` 和 `en-us.ts`
- 新增模块时必须更新 `App.I18n.Schema` 类型约束
- 模板中使用 `$t('key')` 或 `{{ $t('key') }}`

## 环境变量

- 前缀 `VITE_*`，通过 `import.meta.env.VITE_*` 访问
- 环境配置文件：`.env`、`.env.test`、`.env.prod`

## 常用脚本

| 命令 | 说明 |
|------|------|
| `pnpm dev` | 开发模式（测试环境） |
| `pnpm dev:prod` | 开发模式（生产环境） |
| `pnpm build` | 构建生产版本 |
| `pnpm build:test` | 构建测试版本 |
| `pnpm typecheck` | TypeScript 类型检查 |
| `pnpm lint` | ESLint 代码检查与修复 |
| `pnpm gen-route` | 自动生成路由 |
| `pnpm commit:zh` | 交互式 Git 提交 |

## 代码注释

- API 封装函数必须有 JSDoc 注释
- 复杂组件必须有功能描述注释
- 关键业务逻辑必须有行内注释
- 类型声明文件必须有清晰的注释说明
