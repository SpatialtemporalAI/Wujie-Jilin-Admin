---
name: map-editor-read-only-without-edit-permission
description: 地图编辑器无 scene:map-editor:edit 权限时只读：禁用机器人切换地图、禁用右键菜单并提示
metadata:
  type: business
---

# 2026-07-14 地图编辑器无编辑权限时只读

## 需求

地图编辑器中，当用户没有 `scene:map-editor:edit` 权限时，整个编辑器进入只读态：
1. 机器人总览里「切换机器人绑定地图」的下拉禁用（disable）
2. 画布右键菜单禁用——右键时提示「无编辑权限」而非弹出菜单

## 实现

两处统一用 `useAuth().hasAuth('scene:map-editor:edit')` 判断（与保存按钮、删除按钮等现有编辑入口一致的权限码）。

### 机器人切换地图

`frontend/src/views/map-editor/modules/property-panel.vue` 机器人总览 NSelect 加 `:disabled="!hasAuth('scene:map-editor:edit')"`。该文件本就 import 了 `useAuth`。

### 右键菜单

`frontend/src/views/map-editor/index.vue` 的 `handleContextMenu` 入口拦截：

```js
if (!hasAuth('scene:map-editor:edit')) {
  window.$message?.warning('无编辑权限');
  return;  // 不设置 contextMenuShow，菜单不弹出
}
```

`index.vue` 新增 `import { useAuth }` + `const { hasAuth } = useAuth()`。

## 约束与备注

- 右键菜单所有项（添加点位 / 障碍物 / 禁区 / 电子围栏 / 删除）都是编辑操作，无编辑权限时整体禁用，故在入口统一拦截而非逐项 disable
- 切换机器人绑定地图的接口 `PUT /admin/robot/manage/{id}/bind-map` 自身另有权限码，但地图编辑器入口下统一用 `scene:map-editor:edit` 控制只读语义（产品决策：编辑器整体是个编辑场景，无编辑权限即只读，含机器人绑定）
- 与既有只读控制一致：保存按钮 `v-if="hasAuth('scene:map-editor:edit')"`、属性面板/点位列表的删除按钮同理

## 相关文件

- `frontend/src/views/map-editor/modules/property-panel.vue`（机器人总览 NSelect）
- `frontend/src/views/map-editor/index.vue`（`handleContextMenu` 右键入口）
- 参考：`frontend/src/views/map-editor/modules/editor-toolbar.vue`（保存按钮权限用法）

## 记录日期

2026-07-14
