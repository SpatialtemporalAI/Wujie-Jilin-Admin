# 2026-06-11 地图编辑器右侧卡片与机器人总览

## 需求描述

修复地图编辑器右侧卡片存在内容被遮盖的问题，并在右侧卡片中新增“机器人总览”tab，用于快速查看机器人数量、在线状态与基础配置概览。

## 状态

已完成

## 涉及范围

### 后端

无新增或修改后端接口，复用机器人管理列表接口。

### 前端

- 地图编辑器页面布局
- 地图编辑器右侧属性面板
- 机器人管理列表 API 数据展示

## 约束与备注

右侧卡片内容区需要在 tab 头下方独立滚动，避免面板高度继承不完整导致内容被遮挡。右侧卡片 tab 标题栏左右需要保留空白，避免标题贴边。机器人总览复用现有机器人列表接口，不引入新接口。

## 相关文件

- `frontend/src/views/scene/map-editor/index.vue`
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`
- `frontend/src/service/api/robot.ts`
- `frontend/src/typings/api/robot.d.ts`

## 记录日期

2026-06-11
