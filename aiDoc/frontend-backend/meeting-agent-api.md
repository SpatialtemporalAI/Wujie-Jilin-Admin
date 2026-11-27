# 会议管理 · agent 端对接说明

本文档描述「会议管理」模块与机器人 agent 之间的双向接口契约，供 agent 端同事对接使用。

## 总体链路

| 方向 | 场景 | 协议 | 说明 |
|------|------|------|------|
| 平台 → agent | 声纹注册 / 删除声纹 | gRPC `VoiceprintService` | 浏览器录音上传到平台后，平台把音频下发给 agent 做 ASR + 声纹建模 |
| 平台 → agent | 会议模式开 / 关 | gRPC `MeetingModeService` | 平台手动切换机器人会议模式 |
| agent → 平台 | 上传会议音频 | HTTP `POST /openapi/v1/meeting/files` | 上传整场会议录音，拿到 `file_id` |
| agent → 平台 | 上报会议纪要 | HTTP `POST /openapi/v1/meeting/minutes/report` | 按 `meeting_no` 幂等上报会议、发言人、逐字稿、总结 |

---

## 一、平台 → agent（gRPC）

### 1.1 地址与调用约定

- 平台按 `robot.grpc_config.agent` 读取 agent 的 `host:port`，按 `robot_id` 逐台调用；未配置该子键或机器人不存在时不会发起调用。
- 平台侧需开启 `GRPC__ENABLED=true`；单次调用超时为 `GRPC__TIMEOUT_SECONDS`（默认 5 秒）。
- 平台对超时、不可达等异常统一降级处理，不会阻塞主流程：
  - `UNIMPLEMENTED`：视为 agent 未实现该 RPC，平台记录「暂不支持，请升级机器人程序」；
  - 其他 RPC 错误 / 连接失败：平台按「机器人不可达或 agent 未启用」处理。

### 1.2 声纹注册 `VoiceprintService`

proto：[voiceprint.proto](../../backend/grpc/protos/config/voiceprint.proto)

```
package wujie.scene.voiceprint.v1;
service VoiceprintService {
  rpc RegisterVoiceprint(RegisterVoiceprintRequest) returns (RegisterVoiceprintResponse);
  rpc DeleteVoiceprint(DeleteVoiceprintRequest) returns (DeleteVoiceprintResponse);
}
```

#### RegisterVoiceprintRequest

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `robot_id` | int64 | 是 | 目标机器人 ID |
| `role_name` | string | 是 | 发言人姓名 / 角色名称，如 `张工`、`主持人` |
| `role_type` | string | 是 | 角色类型：`主持人` / `发言人` / `记录员` / `旁听` |
| `method` | string | 是 | 录入方式：`record`（整段，当前平台统一使用）/ `stream` |
| `audio` | bytes | 是 | 音频二进制数据（浏览器录音，默认 `webm/opus`，也兼容 wav/mp3/m4a/ogg） |
| `audio_format` | string | 是 | 音频格式，取自上传文件名后缀，如 `webm` |
| `transcript_hint` | string | 否 | 朗读文本提示，供 ASR 校准，可为空 |

#### RegisterVoiceprintResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否注册成功 |
| `message` | string | 失败原因 / 提示 |
| `voiceprint_id` | string | agent 侧声纹 ID，`success=true` 时必填 |
| `transcript` | string | 识别出的文本 |
| `score` | int32 | 声纹质量总分 0-100 |
| `clarity` | int32 | 清晰度 0-100 |
| `match` | int32 | 匹配度 0-100 |
| `noise_level` | string | 噪声等级：`很低` / `低` / `中` / `高` |

#### DeleteVoiceprintRequest / Response

| 字段 | 类型 | 说明 |
|------|------|------|
| `robot_id` | int64 | 目标机器人 ID |
| `voiceprint_id` | string | agent 侧声纹 ID（平台已存） |

Response：`success`(bool)、`message`(string)。

#### 平台侧行为

- 注册失败（`success=false`）或 RPC 异常时，平台仍会写一条 `status=failed` 的声纹记录，`error_msg` 存失败原因，前端据此提示。
- 删除声纹时平台先尽力调用 `DeleteVoiceprint`，远端失败只记日志，不阻断平台侧软删除。

### 1.3 会议模式 `MeetingModeService`

proto：[meeting_mode.proto](../../backend/grpc/protos/config/meeting_mode.proto)

```
package wujie.scene.meeting_mode.v1;
service MeetingModeService {
  rpc SetMeetingMode(SetMeetingModeRequest) returns (SetMeetingModeResponse);
}
```

| 消息 | 字段 | 类型 | 说明 |
|------|------|------|------|
| Request | `robot_id` | int64 | 机器人 ID |
| Request | `enabled` | bool | `true` 进入会议模式，`false` 退出 |
| Response | `success` | bool | 切换动作是否成功 |
| Response | `meeting_mode` | bool | 切换后的最新状态（平台落库 `robot.meeting_mode`） |
| Response | `message` | string | 失败原因 |

- agent 返回 `success=false` 或不可达时，平台抛错并在前端提示，不改变数据库中的会议模式。
- agent 需保证 `meeting_mode` 返回真实状态，平台以该值覆盖本地状态。

---

## 二、agent → 平台（HTTP 开放接口）

### 2.1 通用约定

- Base URL：`{平台地址}/openapi/v1/meeting`
- 鉴权：请求头 `X-Agent-Token: <token>`，与平台配置 `MEETING__AGENT_TOKEN` 一致。
  - 平台该配置为空时不校验（仅建议开发环境）；配置后不匹配返回 `403`，响应 `msg` 为 `X-Agent-Token 无效`。
- 响应结构统一为：

```json
{
  "code": 200,
  "msg": "文件上传成功",
  "data": { },
  "request_id": "uuid",
  "err_code": null
}
```

### 2.2 上传会议音频

`POST /openapi/v1/meeting/files`

- `Content-Type: multipart/form-data`
- 表单字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 会议音频文件（建议 `webm` / `wav` / `mp3`），不能为空 |

响应 `data`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | int | 平台文件 ID，上报纪要及时填到 `audio_file_id` |
| `url` | string \| null | 文件访问地址 |
| `original_name` | string | 原始文件名 |
| `file_size` | int | 文件大小（字节） |
| `mime_type` | string | MIME 类型 |

调用示例：

```bash
curl -X POST "http://{platform}/openapi/v1/meeting/files" \
  -H "X-Agent-Token: {token}" \
  -F "file=@meeting-20261125.webm"
```

### 2.3 上报会议纪要

`POST /openapi/v1/meeting/minutes/report`

- `Content-Type: application/json`

请求体字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `meeting_no` | string(40) | 否 | 会议编号，agent 侧生成的全局唯一编号；缺省由平台生成 `M-YYYYMMDD-XXXXXX` |
| `title` | string(200) | 是 | 会议标题 |
| `robot_id` | int | 是 | 录制机器人 ID（必须已在平台存在） |
| `started_at` | datetime | 是 | 会议开始时间 |
| `duration_seconds` | int | 否 | 会议时长（秒），默认 0 |
| `overview` | string | 否 | 会议概览 / 机器人总结 |
| `conclusions` | array | 否 | 关键结论列表（字符串数组） |
| `risks` | array | 否 | 待确认提醒列表（字符串数组） |
| `summary_generated_at` | datetime | 否 | 总结生成时间 |
| `audio_file_id` | int | 否 | 整场录音文件 ID（先调 `POST /files` 获得）；未传 `audio_url` 时平台据此生成地址 |
| `audio_url` | string(500) | 否 | 整场录音地址，优先于 `audio_file_id` |
| `speakers` | array | 否 | 发言人列表，见下表 |
| `segments` | array | 否 | 逐字稿片段列表，见下表 |

> 业务不需要整场录音时，`audio_file_id` 与 `audio_url` 均可不传：平台侧 `audio_url` 保持为空，前端详情页自动隐藏录音播放条，纪要、发言人、逐字稿的展示与导出不受影响。

`speakers[]`：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `speaker_key` | string(40) | 是 | agent 侧发言人标识，如 `s1`，用于与逐字稿关联 |
| `name` | string(50) | 是 | 发言人姓名 |
| `role` | string(50) | 否 | 角色，如 `主任医师` |
| `color` | string(20) | 否 | 头像颜色标识：`blue` / `purple` / `green` / `orange` |
| `match_score` | int | 否 | 声纹匹配度 0-100 |
| `voiceprint_id` | string(64) | 否 | 关联声纹 ID |
| `sort` | int | 否 | 展示排序，默认 0（按 `sort` 升序，重复时按数组顺序） |

`segments[]`：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `seq` | int | 否 | 片段序号，缺省按数组顺序从 1 递增 |
| `speaker_key` | string(40) | 否 | 发言人标识，需与 `speakers[].speaker_key` 对应 |
| `timecode` | string(16) | 否 | 时间码，如 `04:01` |
| `start_seconds` | float | 否 | 片段起始秒数，用于音频跳转 |
| `text` | string | 是 | 逐字稿文本 |
| `confidence` | int | 否 | 声纹匹配置信度 0-100 |
| `need_confirm` | bool | 否 | 是否为低置信待确认片段，默认 `false` |
| `audio_url` | string(500) | 否 | 片段音频地址 |

响应 `data`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 会议纪要 ID |
| `meeting_no` | string | 最终会议编号（未传时返回平台生成值） |
| `created` | bool | `true` 新建，`false` 覆盖更新 |
| `speaker_count` | int | 本次上报发言人数 |
| `segment_count` | int | 本次上报逐字稿段数 |

请求示例：

```json
{
  "meeting_no": "M-20261125-8F3A21",
  "title": "2026年第四季度护理质控会议",
  "robot_id": 12,
  "started_at": "2026-11-25 09:30:00",
  "duration_seconds": 1860,
  "overview": "会议围绕季度质控指标与护理流程优化展开。",
  "conclusions": ["下季度质控抽查比例提升至 20%"],
  "risks": ["夜间交接班记录仍存在漏填"],
  "summary_generated_at": "2026-11-25T10:05:00+08:00",
  "audio_file_id": 8801,
  "speakers": [
    {"speaker_key": "s1", "name": "张工", "role": "主持人", "color": "blue", "match_score": 92, "sort": 0}
  ],
  "segments": [
    {"seq": 1, "speaker_key": "s1", "timecode": "00:12", "start_seconds": 12.4, "text": "各位同事，会议开始。", "confidence": 95}
  ]
}
```

### 2.4 幂等与覆盖规则

- 平台以 `meeting_no` 为幂等键（**全局唯一**，不同机器人也不应重复）。
- 同 `meeting_no` 重复上报：覆盖主表字段，并**先清空**旧的发言人 / 逐字稿再按本次 payload 重建。请务必每次上报完整的 `speakers` 与 `segments`，不要只传增量。
- 若该会议此前被平台软删除，同 `meeting_no` 再次上报会自动恢复该会议。
- 未传 `meeting_no` 时，平台每次都会生成新编号，即每次上报都会新建一条会议（不适合重试场景）。
- 数据库对 `meeting_no` 建有唯一索引；若重复上报仍出现新建记录，请先比对**响应体里的 `meeting_no`** 与请求是否一致（不一致说明请求未带上该字段，或每次传了不同值）。
- 时间字段兼容 ISO8601（如 `2026-11-25T09:30:00+08:00`、`...Z`）与 `YYYY-MM-DD HH:MM:SS`；无时区信息时按 `Asia/Shanghai` 解析。

### 2.5 常见错误

| HTTP | 场景 | 处理建议 |
|------|------|----------|
| 403 | `X-Agent-Token` 缺失或不匹配 | 检查平台 `MEETING__AGENT_TOKEN` 与请求头是否一致 |
| 404 | `robot_id` 在平台不存在 | 核对机器人 ID（平台机器人管理中的 ID，不是序列号） |
| 422 | 请求体字段类型 / 必填校验失败 | 按上文字段表修正 |
| 500 | 平台内部异常 | 携带 `request_id` 反馈平台侧排查 |

---

## 附：平台后台接口（前端使用，agent 无需调用）

以下接口均需登录态 + 对应权限码，仅供平台 Web 端使用。

| 方法 | 路径 | 权限码 | 用途 |
|------|------|--------|------|
| GET | `/admin/meeting/voiceprint/robots` | `meeting:voiceprint:list` | 声纹页机器人列表（含会议模式、已注册数） |
| GET | `/admin/meeting/voiceprint/overview` | `meeting:voiceprint:list` | 指定机器人的会议模式与已注册声纹数 |
| GET | `/admin/meeting/voiceprint/list` | `meeting:voiceprint:list` | 声纹注册记录分页 |
| POST | `/admin/meeting/voiceprint/register` | `meeting:voiceprint:add` | 浏览器录音上传并下发 agent 建模（multipart） |
| DELETE | `/admin/meeting/voiceprint/{record_id}` | `meeting:voiceprint:delete` | 删除声纹记录（尽力删除 agent 侧声纹） |
| PUT | `/admin/meeting/voiceprint/meeting-mode` | `meeting:voiceprint:meeting_mode` | 开 / 关机器人会议模式 |
| GET | `/admin/meeting/minutes/list` | `meeting:minutes:list` | 会议纪要分页 |
| GET | `/admin/meeting/minutes/trash` | `meeting:minutes:list` | 回收站分页 |
| GET | `/admin/meeting/minutes/{id}` | `meeting:minutes:detail` | 会议详情（含发言人、逐字稿） |
| PUT | `/admin/meeting/minutes/segments/{segment_id}/speaker` | `meeting:minutes:edit` | 人工改派逐字稿发言人 |
| GET | `/admin/meeting/minutes/{id}/export` | `meeting:minutes:export` | 导出纪要（md / txt） |
| DELETE | `/admin/meeting/minutes/{id}` | `meeting:minutes:delete` | 移入回收站 |
| POST | `/admin/meeting/minutes/{id}/restore` | `meeting:minutes:delete` | 从回收站恢复 |
| DELETE | `/admin/meeting/minutes/{id}/purge` | `meeting:minutes:delete` | 彻底删除 |
| DELETE | `/admin/meeting/minutes/trash/clear` | `meeting:minutes:delete` | 清空回收站 |

> 蓝牙设备连接当前仅保留菜单与占位页（权限码 `meeting:bluetooth:list`），设备到位后再补功能。
