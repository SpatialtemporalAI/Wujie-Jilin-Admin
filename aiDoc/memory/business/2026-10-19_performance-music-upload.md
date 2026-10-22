# 表演任务背景音乐支持用户上传（超4分钟自动截取）

## 需求描述

二期八段锦表演任务的背景音乐，原约定「仅预设，不做用户上传」（见 [2026-09-17 会议模式+养生操](./2026-09-17_meeting-mode-and-baduanjin-performance.md) 的约束，现已取代）。本期恢复用户上传：

- 表演步骤的背景音乐可选系统预设曲目，也可上传本地音频（mp3/wav，单个 ≤ 20MB）；
- 上传音频时长超过 5 分钟（300s，2026-10-21 由 4 分钟调整）时，后端自动截取前 5 分钟，UI 有明确文字说明（上传按钮旁提示 + 截取后 toast 提醒）；
- 上传的音乐**仅自己可见**（用户 2026-10-19 明确），支持删除，已被表演任务引用的不允许删除。

## 状态

已完成

## 涉及范围

### 后端

- `modules/task/services/performance_music_service.py`（新增）：ffmpeg 探测时长 + 截取（`imageio-ffmpeg` 自带二进制，无需服务器安装 ffmpeg，截取走 `asyncio.to_thread` 不阻塞事件循环）；上传复用 `core.storage` + `sys_file`；列表仅查 `created_by=当前用户` 的 mp3/wav；删除做所有者校验 + `performance_steps` 文本引用校验（软删除）；`validate_music_refs` 供任务创建/更新校验 `upload:<file_id>` 引用存在性
- `modules/task/endpoints/task.py`：`GET /task/manage/performance/music` 合并预设 + 当前用户上传；新增 `POST /task/manage/performance/music/upload`、`DELETE /task/manage/performance/music/{file_id}`
- `modules/task/schemas/task.py`：`PerformanceStepSchema.music` 放开 `upload:\d+` 校验；`PerformanceMusicOption.duration_seconds` 改 Optional；新增 `PerformanceMusicUploadResult`（`truncated` 标识是否被截取）
- `requirements.txt` 新增 `imageio-ffmpeg>=0.5.1`
- `database/models/business/task.py` + alembic `0018_update_performance_steps_comment.py`（2026-10-21 补充）：`task.performance_steps` 列注释补充 music 取值约定（预设 `bdj_*` / 用户上传 `upload:<sys_file_id>`），仅注释迁移

### 前端

- `task-operate-drawer.vue`：背景音乐 NSelect `action` 插槽放上传入口（mp3/wav 前端预校验）；选中上传音乐时右侧出现删除按钮（NPopconfirm 确认）；底部说明文案补充「超过 4 分钟自动截取前 4 分钟」；上传成功且被截取时 warning toast 明确提示
- `service/api/task.ts` + `typings/api/task.d.ts`：`fetchUploadPerformanceMusic` / `fetchDeletePerformanceMusic` / `PerformanceMusicUploadResult`

## 约束与备注

- `performance_steps.music` 取值约定：预设为 `bdj_*` 标识，用户上传为 `upload:<sys_file_id>`（前后端共用一个前缀常量，后端 `UPLOAD_MUSIC_PATTERN` 校验）
- 时长上限 300s（2026-10-21 由 240s 调整），容忍 0.5s；上限仅约束用户上传，超长按 `-c copy` 流拷贝截取，不重编码；**预设音频不受上限约束**——`bdj_3` 正式文件为 291s 完整版（用户 2026-10-21 确认保留），预设兜底时长已按实际值（225/147/291）写入 `_PERFORMANCE_MUSIC`
- 2026-10-21 调整：背景音乐改为非必填（不选则无配乐，`music` 可为 null）；播放次数限定 1-99999（避免大数显示为科学计数法）；上传成功后不再自动切换当前已选音乐；字段上新增「清除选择」按钮（有值时）与「删除上传音乐」按钮（已选为 upload 时）
- 上传音乐未持久化时长字段：上传响应实时返回时长；列表项时长为实时探测（ffmpeg，并发执行），探测失败返回 null
- 试听：`file_id` 非空即可试听，复用 `GET /admin/sys/file/{file_id}/preview?token=<JWT>`（前端 `getFilePreviewUrl`）。上传音乐 `file_id` 为自身；预设音乐 `file_id` 来自 `sys_file` 种子数据，已种入的预设时长展示音频真实时长
- **预设音频已种子化（2026-10-21，用户确认方案）：alembic `0019_seed_performance_preset_music` 把 `database/seed_assets/performance_music/bdj_{1,2,3}.mp3` 复制到 `uploads/performance_music/` 并插入固定 ID（3000000000000301-303）、`created_by=0` 的 sys_file 行；代码侧 `PRESET_MUSIC_FILE_IDS` 硬编码已删除，改为 `PerformanceMusicService.get_preset_music_file_map` 按 `file_path` 前缀 `performance_music/` 动态查询。`bdj_full_12min` 已于 2026-10-21 从预设目录下线（校验值保留兼容历史任务）。种子行 `created_by=0` 不匹配任何真实用户，天然不会出现在「我上传的音乐」列表**
- 音乐列表数据源是「`created_by=当前用户` 且扩展名为 mp3/wav 的 sys_file」：通过通用文件管理上传的音频也会出现在「我上传的音乐」中（用户 2026-10-20 确认该行为符合预期，"直接用就行了"）
- 前端交互（2026-10-20 改版）：背景音乐改为 `PerformanceMusicSelect` 组件（按钮 + 弹窗），弹窗内完成选择/上传/试听/删除；NUpload `custom-request` 必须调用 `onFinish/onError` 收尾，否则文件滞留队列导致报错累积
- 上传接口路径已加入 `RequestSizeLimitMiddleware` 豁免清单（全局请求体限制 2MB，上传接口按各自大小限制控制）

## 线上部署约束（2026-10-22 补充）

- **文件存储必须与数据库配对**：`sys_file` 记录与 `uploads/` 物理文件是一体的。单实例部署天然一致；迁移服务器时**必须连同 `backend/uploads/` 目录一起迁移**；多实例部署必须把 `UPLOAD_LOCAL.BASE_DIR` 指向共享存储（NFS/共享盘），否则会出现「记录存在但文件缺失」（试听 404、时长探测失败）
- 开发环境踩坑实例：多人共用一个开发库 + 各自本机存储，A 机器上传的音频在 B 机器无法播放/探测时长。预设音频已通过 alembic 0019 种子化规避；用户上传音频靠 `validate_music_refs` 的物理存在校验兜底
- 长期方案：`core.storage` 已抽象存储后端（当前仅 local），需要时扩展 S3/MinIO 后端即可彻底消除该问题
- 兜底逻辑（2026-10-22）：创建/更新任务时 `validate_music_refs` 同时校验「DB 记录存在」与「存储文件物理存在」，缺一即拒绝保存并提示重新上传；前端对失效引用（文件已删除/不可见）加载选项后**直接置空**，不回退展示 `upload:<id>` 原始标识；歌名超长时按钮文本超出省略（truncate + title 悬停显示完整名）
- 物理文件不随删除清理（与系统文件管理软删除行为一致）
- 2026-10-22 事故记录：一条表演任务步骤 `music` 为 null（非 API 写入，API 创建/更新均有 `PerformanceStepSchema` 严格校验），`TaskResponseData` 严格序列化导致整个任务列表 422「数据验证失败」。处理：脏数据修复（删除该套动作）+ `TaskResponseData.performance_steps` 改宽松 dict（同 `TaskDefinitionSnapshot` 思路），写入侧校验保持严格
- 机器人端播放上传音乐需按 `upload:<file_id>` 自行拉取文件（可走 preview/download 链路，preview 支持 `?token=` 与签名 URL），agent 侧配套不在本次范围

## 相关文件

- 后端：`backend/modules/task/services/performance_music_service.py`、`backend/modules/task/endpoints/task.py`、`backend/modules/task/schemas/task.py`、`backend/modules/task/services/task_service.py`、`backend/requirements.txt`
- 前端：`frontend/src/views/task/modules/task-operate-drawer.vue`、`frontend/src/service/api/task.ts`、`frontend/src/typings/api/task.d.ts`

## 记录日期

2026-10-19
