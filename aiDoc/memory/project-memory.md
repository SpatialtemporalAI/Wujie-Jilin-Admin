# 项目记忆索引

本文件是 `aiDoc/memory/` 的总入口。

## 长期记忆

暂无。

## 业务需求记忆

- [2026-06-11 机器人配置迁移修复](./business/2026-06-11_robot-config-migration-fix.md) — 修复 robot_voice_config 存量表缺少 robot_id 导致语音配置接口 500
- [2026-06-11 人脸识别人像预览路径修复](./business/2026-06-11_face-photo-preview-path.md) — 避免持久化带 token 的完整预览 URL 导致 photo_url 超长 422
- [2026-06-11 人脸识别删除修复](./business/2026-06-11_face-delete-fix.md) — 修复删除配置时错误调用 soft_delete，并补齐移除人像清空字段
- [2026-06-11 人脸识别人像上传接口修复](./business/2026-06-11_face-upload-endpoint.md) — 新增机器人配置专用上传接口，避免上传人像 404
- [2026-06-11 机器人参数配置选择机器人布局调整](./business/2026-06-11_robot-config-select-layout.md) — 行走速度和电量报警阈值改为下拉选择机器人后读取配置
- [2026-06-11 地图编辑器右侧卡片与机器人总览](./business/2026-06-11_map-editor-right-panel-robot-overview.md) — 修复右侧卡片遮盖并新增机器人总览 tab
- [2026-06-11 地图编辑器机器人定位与绑定场景](./business/2026-06-11_map-editor-robot-location-binding.md) — 机器人总览列表支持定位与切换绑定场景
- [2026-06-11 场景地图 JSON 点位导入](./business/2026-06-11_scene-map-json-import.md) — 地图编辑器支持将 label/position JSON 导入为标注点
- [2026-06-11 机器人场景绑定可空与存量库缺列修复](./business/2026-06-11_robot-map-binding-nullable-fix.md) — robot.map_id 缺列自动补齐，未绑定场景不支持定位
- [2026-06-11 地图编辑器新增场景图片与起始点位](./business/2026-06-11_map-editor-create-scene-image-start-point.md) — 新增场景上传图片并按原图/网页显示尺寸缩放保存起始点位
- [2026-06-17 场景地图新增导航地图图片](./business/2026-06-17_scene-map-nav-image.md) — 异步将障碍物/禁区绘制到原图副本生成 nav_image_id
- [2026-06-17 机器人管理移除列表状态列](./business/2026-06-17_robot-manage-remove-status-column.md) — 去掉机器人管理表格中的状态显示列
- [2026-06-17 场景地图新增映射比例输入](./business/2026-06-17_scene-map-resolution-input.md) — 新增/编辑场景地图时填写 resolution，默认 1
- [2026-06-17 任务管理页面白色卡片背景调整](./business/2026-06-17_task-page-card-background.md) — 任务管理页增加白色卡片容器以修正 UI 样式偏差
- [2026-06-17 地图编辑器、机器人新增与任务管理修复](./business/2026-06-17_editor-robot-task-fixes.md) — 调整地图编辑器交互/默认值、机器人新增默认配置并修复任务页空白
- [2026-06-17 场景地图、任务列表与运行监控 UI 修复](./business/2026-06-17_scene-task-monitor-ui-fixes.md) — 修复图片预览、任务表格/禁用操作和运行监控地图布局
- [2026-06-17 任务新增编辑必填校验](./business/2026-06-17_task-form-required-validation.md) — 巡逻点位/动作和定时日期/开始时间提交前必填校验
- [2026-06-17 任务启用禁用按钮修复](./business/2026-06-17_task-toggle-enabled-fix.md) — 统一任务列表 enabled 状态转换，修复切换按钮无反应
- [2026-06-17 任务地图优先选择与点位删除联动](./business/2026-06-17_task-map-selection-and-point-cascade.md) — 任务先选地图、列表支持地图/机器人筛选，并联动删除任务点位

## 维护说明

- 新增记忆时，在对应目录创建 Markdown 文件，并在此索引中添加条目
- 过时的记忆应及时清理
- 记忆文件应包含日期标记，便于判断时效性
