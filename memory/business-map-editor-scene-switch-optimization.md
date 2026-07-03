---
name: business-map-editor-scene-switch-optimization
description: 优化地图编辑器的场景地图切换逻辑，统一切换入口并增加脏状态保护。
metadata:
  type: business
---

**需求内容**：优化地图编辑器（`frontend/src/views/scene/map-editor/`）的场景地图切换逻辑。

**核心改动**：
- 在 `useMapEditor.ts` 中新增 `switching` 状态，强化 `loadMap` 的错误处理，调整 `deleteScene` 返回值以支持页面层决策。
- 在 `index.vue` 中新增统一的 `switchMap` 切换守卫，提供「保存并切换 / 不保存切换 / 取消」三按钮确认。
- 覆盖所有切换入口：初始加载、左侧场景列表点击、新建场景、编辑当前场景、删除场景、机器人跨场景定位。
- 新增相关 i18n 键（`page.sceneMapEditor.*`）并同步类型声明。

**验收标准**：
- 有未保存修改时切换场景必须二次确认。
- 快速连续点击场景只执行一次切换。
- 地图加载失败时保持当前场景状态并提示错误。
- `pnpm typecheck` 通过（仅关注本次改动文件，项目存在历史遗留类型错误）。

**相关记忆**：[[business-map-editor-delete-hotkey]]
