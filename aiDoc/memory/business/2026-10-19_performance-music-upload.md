# 表演任务背景音乐支持用户上传（超4分钟自动截取）

## 需求描述

二期八段锦表演任务的背景音乐，原约定「仅预设，不做用户上传」（见 [2026-09-17 会议模式+养生操](./2026-09-17_meeting-mode-and-baduanjin-performance.md) 的约束，现已取代）。本期恢复用户上传：

- 表演步骤的背景音乐可选系统预设曲目，也可上传本地音频（mp3/wav，单个 ≤ 20MB）；
- 上传音频时长超过 4 分钟（240s）时，后端自动截取前 4 分钟，UI 有明确文字说明（上传按钮旁提示 + 截取后 toast 提醒）；
- 上传的音乐**仅自己可见**（用户 2026-10-19 明确），支持删除，已被表演任务引用的不允许删除。

## 状态

已完成

## 涉及范围

### 后端

- `modules/task/services/performance_music_service.py`（新增）：ffmpeg 探测时长 + 截取（`imageio-ffmpeg` 自带二进制，无需服务器安装 ffmpeg，截取走 `asyncio.to_thread` 不阻塞事件循环）；上传复用 `core.storage` + `sys_file`；列表仅查 `created_by=当前用户` 的 mp3/wav；删除做所有者校验 + `performance_steps` 文本引用校验（软删除）；`validate_music_refs` 供任务创建/更新校验 `upload:<file_id>` 引用存在性
- `modules/task/endpoints/task.py`：`GET /task/manage/performance/music` 合并预设 + 当前用户上传；新增 `POST /task/manage/performance/music/upload`、`DELETE /task/manage/performance/music/{file_id}`
- `modules/task/schemas/task.py`：`PerformanceStepSchema.music` 放开 `upload:\d+` 校验；`PerformanceMusicOption.duration_seconds` 改 Optional；新增 `PerformanceMusicUploadResult`（`truncated` 标识是否被截取）
- `requirements.txt` 新增 `imageio-ffmpeg>=0.5.1`

### 前端

- `task-operate-drawer.vue`：背景音乐 NSelect `action` 插槽放上传入口（mp3/wav 前端预校验）；选中上传音乐时右侧出现删除按钮（NPopconfirm 确认）；底部说明文案补充「超过 4 分钟自动截取前 4 分钟」；上传成功且被截取时 warning toast 明确提示
- `service/api/task.ts` + `typings/api/task.d.ts`：`fetchUploadPerformanceMusic` / `fetchDeletePerformanceMusic` / `PerformanceMusicUploadResult`

## 约束与备注

- `performance_steps.music` 取值约定：预设为 `bdj_*` 标识，用户上传为 `upload:<sys_file_id>`（前后端共用一个前缀常量，后端 `UPLOAD_MUSIC_PATTERN` 校验）
- 时长上限 240s，容忍 0.5s（240.3s 之类不重新转码）；截取用 `-c copy` 流拷贝，不重编码
- 上传音乐未持久化时长字段：上传响应实时返回时长；列表项时长为实时探测（ffmpeg，并发执行），探测失败返回 null
- 试听：`file_id` 非空即可试听，复用 `GET /admin/sys/file/{file_id}/preview?token=<JWT>`（前端 `getFilePreviewUrl`）。上传音乐 `file_id` 为自身；预设音乐通过在文件管理上传音频后、把 sys_file_id 填入后端 `_PRESET_MUSIC_FILE_IDS`（`modules/task/endpoints/task.py`）开通试听，已映射的预设时长展示音频真实时长
- **当前 `_PRESET_MUSIC_FILE_IDS` 映射的是测试环境 sample-audio-* 文件（用户 2026-10-20 确认"当作正式文件"），正式环境部署时必须替换为正式预设音频的 sys_file_id**
- 音乐列表数据源是「`created_by=当前用户` 且扩展名为 mp3/wav 的 sys_file」：通过通用文件管理上传的音频也会出现在「我上传的音乐」中（用户 2026-10-20 确认该行为符合预期，"直接用就行了"）
- 前端交互（2026-10-20 改版）：背景音乐改为 `PerformanceMusicSelect` 组件（按钮 + 弹窗），弹窗内完成选择/上传/试听/删除；NUpload `custom-request` 必须调用 `onFinish/onError` 收尾，否则文件滞留队列导致报错累积
- 上传接口路径已加入 `RequestSizeLimitMiddleware` 豁免清单（全局请求体限制 2MB，上传接口按各自大小限制控制）
- 物理文件不随删除清理（与系统文件管理软删除行为一致）
- 机器人端播放上传音乐需按 `upload:<file_id>` 自行拉取文件（可走 preview/download 链路，preview 支持 `?token=` 与签名 URL），agent 侧配套不在本次范围

## 相关文件

- 后端：`backend/modules/task/services/performance_music_service.py`、`backend/modules/task/endpoints/task.py`、`backend/modules/task/schemas/task.py`、`backend/modules/task/services/task_service.py`、`backend/requirements.txt`
- 前端：`frontend/src/views/task/modules/task-operate-drawer.vue`、`frontend/src/service/api/task.ts`、`frontend/src/typings/api/task.d.ts`

## 记录日期

2026-10-19
