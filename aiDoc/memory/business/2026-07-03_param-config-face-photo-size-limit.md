# 参数配置·人脸识别TTS 人像上传限制（对齐阿里云 facebody 规格）

## 需求描述

「参数配置 - 人脸识别TTS」tab 上传人像时，按阿里云 facebody 要求限制输入，并在人像输入框右侧增加说明：

- 图像格式：JPG、JPEG、PNG
- 图像大小：不超过 5 MB
- 图像分辨率：大于 32×32 像素，小于 4096×4096 像素
- 人脸占比：不低于 64×64 像素（由 facebody 校验，本服务不做）
- 图片中若包含多个人脸，会取最大的人脸进行添加（facebody 行为）

语音合成（TTS）tab 仅为参数配置（音色/语速/音量/唤醒词），无文件上传，不涉及。

## 状态

已完成（前端 + 后端）。`pnpm typecheck` 通过（本次改动文件无新增报错；既有 `locales/langs` 的 `map-editor` 路由 i18n 报错与本次无关）。

## 涉及范围

### 后端

`backend/modules/robot/endpoints/robot_config.py` 的 `upload_face_photo`（`POST /robot/config/face/upload`）：

- 新增常量 `ALLOWED_FACE_PHOTO_EXTS=("jpg","jpeg","png")`、`MAX_FACE_PHOTO_SIZE=5*1024*1024`、`MIN_FACE_PHOTO_DIM=32`、`MAX_FACE_PHOTO_DIM=4096`；
  新增 `from core.storage import validate_file_size, validate_file_extension` + `from core.exception.errors import RequestError`。
- 读 `file_data = await file.read()` 后依次校验：`validate_file_size(...,MAX_FACE_PHOTO_SIZE)` → `validate_file_extension(filename, ALLOWED_FACE_PHOTO_EXTS)` → `FileService.get_image_dimensions(file_data, mime)` 取宽高，超出 32×32~4096×4096 区间抛 `RequestError("图像分辨率需大于 32×32 ... 当前 WxH")`。
- 校验放 Endpoint 层而非 `FileService.upload_file`：5MB / 格式 / 分辨率均人脸专用，通用上传仍走全局 `UPLOAD_LOCAL.MAX_FILE_SIZE`(默认 10MB) 与全局扩展名白名单，互不影响。
- 人脸占比 64×64 不在此校验（本服务无人脸检测能力），由 facebody 注册时报错，经 [[2026-07-01_param-config-face-aliyun-error-parse]] 的错误解析友好化提示。

### 前端

`frontend/src/views/settings/modules/face-recognition-tab.vue`：

- 常量：`ALLOWED_FACE_PHOTO_EXTS`、`MAX_FACE_PHOTO_SIZE=5MB`、`MIN_FACE_PHOTO_DIM=32`、`MAX_FACE_PHOTO_DIM=4096`。
- 新增 `getImageSize(file)`：`URL.createObjectURL` + `Image.onload` 读宽高，失败返回 null。
- `handleUpload`（NUpload custom-request）上传前依次校验：扩展名(jpg/jpeg/png)、大小(≤5MB)、分辨率(>32 且 <4096)，任一不过则 `message.error(中文提示)` + 清空 `fileList` + `return`，不发请求；人脸占比不在前端校验。
- NUpload `accept` 由 `image/*` 收紧为 `.jpg,.jpeg,.png,image/jpeg,image/png`。
- 人像输入框布局改为左右两栏（`.face-upload-wrap` flex）：左侧 NUpload + 已上传文案，右侧 `.face-upload-tips` 列出 5 条说明（格式/大小/分辨率/人脸占比/多脸取最大）；窄屏（≤768px）自动堆叠。

## 约束与备注

- 前后端各加一道校验：前端体验（即时提示、不发请求），后端兜底（防绕过 NUpload 直调接口）；人脸占比仅 facebody 能校验。
- 复用项目既有 `validate_file_size` / `validate_file_extension` / `FileService.get_image_dimensions`，未改通用 FileService。
- 后端改动需重启 FastAPI 服务才生效。
- 与 [[2026-06-30_param-config-face-aliyun-direct]] 同属「参数配置·人脸识别TTS」链路：上传走本地 FileService 落盘，人脸注册由 FaceService 直连阿里云 facebody。
- 演进：本条最初为「2MB 大小限制」，后按阿里云 facebody 规格升级为「5MB + 格式 + 分辨率 + 右侧说明」。

## 相关文件

- `frontend/src/views/settings/modules/face-recognition-tab.vue`
- `backend/modules/robot/endpoints/robot_config.py`
- 校验工具（未改）：`backend/core/storage/validator.py`、`backend/modules/admin/services/sys/file_service.py`（`get_image_dimensions`）

## 记录日期

2026-07-03
