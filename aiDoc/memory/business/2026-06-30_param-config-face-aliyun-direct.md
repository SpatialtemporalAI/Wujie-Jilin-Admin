# 参数配置 · 人脸识别改为直连阿里云 facebody

## 需求描述

「参数配置」页的人脸识别此前是：本地落库 `robot_face_recognition` 后，通过内部 gRPC（`FaceRecognitionClient.notify_changed`）
把增量广播给所有启用 agent 的机器人，按推送结果返回 `grpc_status`（synced/pending_retry/disabled）。

需求：人脸识别**不再走 gRPC 推送**，改为在增删改时**直接调用阿里云 facebody（已有的 `FaceService`）**，
把每条本地记录注册为人脸库 `lvya` 中的一个 entity（含人脸图片），并在本地记录中保存阿里云 `entity_id`。

## 状态

已完成（后端 + 前端 + 迁移）。需 `alembic upgrade head` 应用 0038；假设阿里云侧已存在人脸库 `lvya`
（若无，先用「人脸库管理」页 manage/face 新建一次，`add_face_entity` 不会自动建库）。

## 关键决策（与用户确认）

| 项 | 决策 |
|---|---|
| 阿里云注册失败 | **回滚本地记录**（整个保存失败、前端报错，本地不留残桩） |
| `entity_id` 取值 | **`str(face.id)`**（本地记录主键字符串） |
| gRPC 清理范围 | 停止调用 + 移除 `retry_service` 中 face 路由；**保留** `FaceRecognitionClient` 类与 `face_recognition` proto/pb2 不删 |
| 编辑换图 | **替换**：先 `add_face_image` 入新图、再 best-effort `delete_face` 删旧图（本地额外存 `face_id`） |

一致性语义区分：create/update 的注册类步骤失败 → 回滚本地（含 best-effort 补偿删刚建的 entity）；
delete 以本地为准，阿里云删除偶发失败仅告警、不阻塞本地删除。

## 涉及范围

### 后端

- `backend/database/models/business/robot_face_recognition.py`：新增 `entity_id` / `face_id`（String(64)，nullable）
- `backend/database/alembic/versions/0038_robot_face_entity.py`：`ALTER TABLE … ADD COLUMN` 两列（downgrade 反向 drop）
- `backend/modules/face/services/face_service.py`：抽出私有 `_upload_bytes_to_oss(file_data, ext)`，
  新增对外 `upload_bytes_to_oss`；`upload_to_oss(UploadFile)` 改为读字节后转调（manage/face 仍用旧签名）
- `backend/modules/robot/services/robot_config_service.py`：
  - 模块常量 `_FACE_DB_NAME = "lvya"`；`_PHOTO_FILE_ID_RE` 解析 photo_url 中的 file_id
  - `_file_id_from_photo_url` / `_upload_photo_to_aliyun_oss`（读本地字节→传阿里云 OSS）
  - 重写 `create_face` / `update_face` / `delete_face`：移除 `FaceRecognitionClient` 调用，
    改调 `FaceService.add_face_entity` / `add_face_image` / `delete_face` / `delete_face_entity`
  - 不再导入 `FaceRecognitionClient`；voice/speed/battery 仍走 `_push_with_retry` 不变
- `backend/modules/robot/schemas/robot_config.py`：`RobotFaceRecognitionResponse` 增 `entity_id` / `face_id`
- `backend/modules/grpc/retry_service.py`：删 `_ROUTING` 中 `face_recognition/NotifyFaceRecognitionChanged`
  及 `_superseded_clause` 的 face 特判；不再导入 `FaceRecognitionClient`
- `backend/modules/robot/endpoints/robot_config.py`：face 三端点逻辑不变（status 恒 synced，复用 `_GRPC_MSG_MAP`）
- `FaceRecognitionClient` 类、`face_recognition.proto` / `*_pb2*.py` 保留未删（不再被调用）

### 前端

- `frontend/src/typings/api/robot-config.d.ts`：`FaceRecognition` 加 `entity_id?` / `face_id?`
- `frontend/src/views/settings/modules/face-recognition-tab.vue`：
  去掉 `grpc_status === 'pending_retry'` 的「（设备同步待重试）」分支（face 该状态不再出现），
  统一提示「保存/更新/删除成功」；列表新增「实体ID」列便于核对已注册（scroll-x→720）

## 约束与备注

- 图片来源：复用参数配置既有 `/face/upload`（本地存储，photo_url = `/admin/sys/file/{id}/preview`）；
  create/update 时按 file_id 读回字节 → `FaceService.upload_bytes_to_oss` 传阿里云托管 OSS（临时 URL，仅用于 AddFace，不落库）
- entity_id = str(face.id)：本地记录与阿里云 entity 一一对应；旧记录 entity_id 为空，换图更新时懒建实体
- 跨系统一致性边界：create 中「建实体成功 + 入图失败」会 best-effort 补偿删实体；update 换图「入新图成功 + 删旧图失败」仅告警（新图已注册不回滚）；delete 阿里云失败仅告警。跨本地+阿里云的完美 2PC 不做
- 与 [[2026-06-29_face-recognition-aliyun]] 区别：那次是独立的「人脸库管理」模块（manage/face，库级增删查）；
  本次是「参数配置」里的人员 TTS 配置改直连同一 facebody，二者复用 `FaceService` 但表与入口独立
- 与 [[2026-06-25_param-config-grpc-from-robot]] 关系：那次让人脸走 gRPC 广播到 robot agent，本次反转为不走 gRPC、直连阿里云

## 相关文件

- 模型/迁移：`backend/database/models/business/robot_face_recognition.py`、`backend/database/alembic/versions/0038_robot_face_entity.py`
- 服务：`backend/modules/robot/services/robot_config_service.py`、`backend/modules/face/services/face_service.py`
- schema/retry：`backend/modules/robot/schemas/robot_config.py`、`backend/modules/grpc/retry_service.py`
- 前端：`frontend/src/typings/api/robot-config.d.ts`、`frontend/src/views/settings/modules/face-recognition-tab.vue`

## 记录日期

2026-06-30
