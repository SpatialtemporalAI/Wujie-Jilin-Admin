# 参数配置·人脸识别编辑修复（按钮无反应 + 编辑不可改图）

## 需求描述

「参数配置 - 人脸识别TTS」列表的「编辑」按钮点击后没有可见反馈（表单在列表上方，用户滚到下方点编辑时看不到表单已回填，表现为「点了没反应」）。
同时要求：**编辑时人像不可修改**，仅允许修改「人员名称」和「播报内容」。

## 状态

已完成（前端）。`pnpm typecheck` 通过（无新增报错）。

## 涉及范围

### 后端

无改动。复用既有 `update_face`：`photo_changed = "photo_url" in update_data and update_data["photo_url"] != face.photo_url`
（`backend/modules/robot/services/robot_config_service.py`）。编辑时前端原样回传未变更的 `photo_url`，
后端判定 `photo_changed=False`，自动跳过阿里云换图（add_face_image/delete_face），仅更新名称与播报文字。

### 前端

`frontend/src/views/settings/modules/face-recognition-tab.vue`：

- `handleEdit` 点击后：强制展开表单 `isFormExpanded=true` → `restoreValidation()` 清旧校验 →
  `nextTick` 内 `formAnchorRef.scrollIntoView({ behavior:'smooth', block:'start' })`，把上方表单滚入视口，
  解决「点了没反应」。
- 表单卡片标题随模式切换：编辑态显示「编辑人脸识别TTS」，新建态显示「配置人脸识别TTS」。
- 人像表单项按模式分流：
  - `editingId` 为真（编辑）：渲染只读 `<img>` 预览 + 文案「编辑时不支持修改人像」，不渲染 NUpload。
  - 否则（新建）：保持原 NUpload 上传与 `path="photo_url"` 校验。

## 约束与备注

- 编辑保存仍调用 `fetchUpdateFaceRecognition(id, { person_name, broadcast_text, photo_url })`，
  其中 `photo_url` 为回填的原值（未改）。前端类型 `FaceRecognitionCreate` 仍要求 `photo_url`，故保留回传，
  不改前后端契约。
- 后端 `update_face` 用 `exclude_unset=True` 取差量；即便将来前端改为不传 `photo_url`，后端也会判 `photo_changed=False`。
- 与 [[2026-06-30_param-config-face-aliyun-direct]] 一致：换图能力在后端保留，仅前端编辑入口屏蔽改图。
- 既有 unrelated typecheck 报错位于 `src/views/scene/map/*`，与本次改动无关。

## 相关文件

- `frontend/src/views/settings/modules/face-recognition-tab.vue`
- 后端逻辑参考（未改）：`backend/modules/robot/services/robot_config_service.py`

## 记录日期

2026-07-01
