# 参数配置·人脸识别 阿里云错误信息友好化解析

## 需求描述

「参数配置」页人脸识别 TTS 在增删改时直连阿里云 facebody（见 [[2026-06-30_param-config-face-aliyun-direct]]）。
当阿里云接口返回错误（典型：添加人脸图片时图片中无人脸，`InvalidImage.NotFoundFace`），
此前会把 SDK 异常的 `str(exc)` 原样塞进 `GatewayError.msg`，导致前端 toast 弹出一长串技术信息：

```
添加人脸图片失败: Error: InvalidImage.NotFoundFace code: 404, [pk=...,tag=viapi:default]
input image not found face request id: ... Response: {'RequestId':..., 'Code':..., 'Message':..., ...}
```

需求：把阿里云接口错误解析成**可读的中文异常提示**展示给用户。

## 状态

已完成（纯后端）。前端无需改动——前端请求拦截器 `onError` 直接读后端统一响应里的 `msg`
（`responseData.msg`）并 `$message.error`，所以后端 `msg` 干净，前端 toast 就干净。

## 方案

`backend/modules/face/services/face_service.py` 新增：

- `_FACE_ERROR_HINT`：阿里云 facebody 常见错误码 → 中文友好提示的映射表
  （`InvalidImage.NotFoundFace` → 「未在图片中检测到人脸，请使用清晰正面的真人照片」等）
- `_FACE_ERROR_NOISE_RE`：抹掉 message 里 `[pk=...,tag=viapi:default]` 这类内部噪声前缀
- `_describe_aliyun_error(exc)`：从 SDK 异常取 `code` / `message`（getattr 兼容大小写），
  命中已知码给中文提示，否则回退清洗后的 message，再否则 `str(exc)`；统一输出
  `中文提示（错误码：XXX）` 形式

所有调用 facebody / viapi OSS 的 `except Exception` 改为：

- `GatewayError(msg=f"xxx失败: {_describe_aliyun_error(exc)}")` —— 用户看到的是干净提示
- `logger.error("xxx失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)` —— 服务端日志仍保留
  完整原始异常（含 RequestId / Response），便于排障

覆盖方法：create_face_db / list_face_dbs / add_face_entity / delete_face_entity /
list_face_entities / get_face_entity / add_face_image / delete_face / search_face / detect_face，
以及 viapi `_upload_bytes_to_oss`。

## 约束与备注

- 前端零改动：错误展示完全依赖后端 `msg`，符合统一响应结构 `{code, msg, data, ...}`
- 未做错误码穷举：未知错误码回退到「清洗后 message（错误码：XXX）」，保证不再裸抛 `Response` 字典；
  后续遇到新的高频错误码可直接往 `_FACE_ERROR_HINT` 加
- 与 [[2026-06-29_face-recognition-aliyun]] 的「人脸库管理」模块共用同一 `FaceService`，
  因此本次修复对 manage/face 页面同样生效

## 相关文件

- `backend/modules/face/services/face_service.py`（新增 `_FACE_ERROR_HINT` / `_describe_aliyun_error`，
  改写全部 facebody + OSS except 块）

## 记录日期

2026-07-01
