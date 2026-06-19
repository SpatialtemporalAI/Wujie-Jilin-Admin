# 运行监控页面滚动 + 登录后底部栏隐藏

## 需求描述

1. 运行监控（operation-monitor）页面整体允许纵向滚动：当窗口高度不足以容纳机器人状态卡片、Tab 内容（实时位置/实时告警、视频监控）时，整个页面可以通过滚动查看全部内容，而不是被裁剪。
2. 登录后默认不再显示底部栏（GlobalFooter）。

## 状态

已完成

## 涉及范围

### 后端

无

### 前端

- `frontend/src/views/operation-monitor/index.vue`：去除原本 `overflow-hidden` + `flex-col-stretch` 撑满高度布局，改为 `overflow-y-auto` 纵向滚动；地图与实时告警区域各固定 `h-520px` 高度。
- `frontend/src/theme/settings.ts`：
  - `themeSettings.footer.visible` 由 `true` 改为 `false`，覆盖开发环境与新用户首次进入生产环境。
  - 新增 `overrideThemeSettings.footer`（visible=false），保证老用户在生产环境部署新版本时强制覆盖 localStorage 中缓存的旧配置。

## 约束与备注

- 主题抽屉中"底部栏"开关仍然可用，用户主动开启仍能恢复显示，仅修改默认值。
- 主题预设 `preset/default.json`、`preset/dark.json` 中 `footer.visible` 仍为 `true`，用户主动应用预设时可能恢复底部栏，未做同步修改（preset 是用户主动行为）。
- 地图（PositionMapPanel 内部 fabric.Canvas）与实时告警（AlertPanel 内部 `overflow-y-auto`）在固定 520px 高度下保留各自原生的滚动 / 缩放行为。

## 相关文件

- `frontend/src/views/operation-monitor/index.vue`
- `frontend/src/theme/settings.ts`

## 记录日期

2026-06-18
