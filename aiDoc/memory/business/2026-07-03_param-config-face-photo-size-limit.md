# 参数配置·人脸识别TTS 人像上传增加 2MB 文件大小限制

## 需求描述

「参数配置 - 人脸识别TTS」tab 上传人像时，需限制单张图片大小不超过 **2MB**，超限拒绝上传并提示用户。
语音合成（TTS）tab 仅为参数配置（音色/语速/音量/唤醒词），无文件上传，不涉及。

## 状态

已完成（前端 + 后端）。`pnpm typecheck` 通过（本次改动文件无新增报错；既有 `locales/langs` 的 `map-editor` 路由 i18n 报错与本次无关）。

## 涉及范围

### 后端

`backend/modules/robot/endpoints/robot_config.py` 的 `upload_face_photo`（`POST /robot/config/face/upload`）：

- 顶部新增常量 `MAX_FACE_PHOTO_SIZE = 2 * 1024 * 1024`，并 `from core.storage import validate_file_size`。
- 读 `file_data = await file.read()` 后、调 `FileService.upload_file` 前，先 `validate_file_size(len(file_data), MAX_FACE_PHOTO_SIZE)`，
  超限抛 `RequestError(msg="文件大小超过限制，最大允许 2.0MB")`。
- **校验放在 Endpoint 层而非 `FileService.upload_file`**：2MB 是人脸识别专用上限，通用上传仍保持全局 `UPLOAD_LOCAL.MAX_FILE_SIZE`（默认 10MB），互不影响。

### 前端

`frontend/src/views/settings/modules/face-recognition-tab.vue`：

- 顶部新增常量 `MAX_FACE_PHOTO_SIZE = 2 * 1024 * 1024`。
- `handleUpload`（NUpload 的 custom-request）在发起上传前先判 `file.file.size > MAX_FACE_PHOTO_SIZE`，
  超限则 `message.error('人像文件大小不能超过 2MB')` + 清空 `fileList` + `return`，不发请求。
- 编辑模式人像只读、不上传，故本次只作用于新建模式的上传分支。

## 约束与备注

- 前后端各加一道校验：前端为体验（即时提示、不发请求），后端为兜底（防绕过 NUpload 直接调接口）。
- 复用项目既有 `validate_file_size` 工具（`backend/core/storage/validator.py`），与通用文件上传同一报错文案风格。
- 后端改动需重启 FastAPI 服务才生效。
- 与 [[2026-06-30_param-config-face-aliyun-direct]] 同属「参数配置·人脸识别TTS」链路：上传走本地 FileService 落盘，人脸注册仍由 FaceService 直连阿里云 facebody。

## 相关文件

- `frontend/src/views/settings/modules/face-recognition-tab.vue`
- `backend/modules/robot/endpoints/robot_config.py`
- 校验工具（未改）：`backend/core/storage/validator.py`

## 记录日期

2026-07-03
