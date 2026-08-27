# 语音问诊模块（会话记录 + 统计分析页）

## 需求描述

1. 新增「语音问诊」模块，记录机器人语音问诊交互数据，字段：时间、触发方式、机器人、轮次、提问摘要、时长、状态、意图类型（**2026-08-27 起意图类型仅保留在轮次维度**，会话级展示/筛选/导出全部移除）。
2. **数据由其它应用直连数据库写入**（本系统不开发写入接口），本系统负责建表 + 管理端查询/统计/详情/导出 API + 前端展示页。
3. 一次会话含多轮问答，「查看」详情展示完整对话，故为两张表（会话主表 + 轮次明细表）。
4. 前端布局按参考图：顶部 3 统计卡片（总交互/今日交互/平均会话时长带环比）→ 中部两图（意图分布横向柱状图 + 触发方式环形图）→ 底部筛选栏 + 「问答记录」表格 + 分页 + 导出。

## 枚举约定（外部写入方需遵守）

- `intent_type` 意图 6 种：`indoor_navigation` 院内问路 / `triage_qa` 分诊问答 / `medical_guide` 就医指南 / `health_check_notice` 体检须知 / `insurance_guide` 医保指南 / `admission_notice` 住院须知（2026-08-26 起移除 `medication_consult` 药物咨询、`general_chat` 闲聊寒暄）
- `trigger_method` 触发 2 种：`wake_word` 唤醒词 / `face_recognition` 人脸识别
- `status` 状态 3 种：`in_progress` 进行中 / `completed` 已完成 / `interrupted` 已中断

## 状态

已完成（后端 + 前端 + 迁移 + typecheck 通过；`alembic upgrade head` 待用户在有 DB 环境执行）

## 涉及范围

### 后端

- **Model**：`database/models/business/voice_consultation_session.py`（`VoiceConsultationSession`：robot_id FK、occurred_at 交互时间、trigger_method、turn_count 冗余轮次、question_summary、duration_seconds、status、intent_type）、`voice_consultation_turn.py`（`VoiceConsultationTurn`：session_id FK、turn_no、question/answer Text、intent_type、duration_seconds、occurred_at）。两模型已注册 `business/__init__.py` + `alembic/env.py` 模块元组。
- **模块**：`modules/voice_consultation/`（endpoints/schemas/services + router，`prefix="/voice-consultation"`），挂 `modules/admin/router.py`，最终路径 `/admin/voice-consultation/sessions/{list,stats,{id}}`。权限码 `voice:consultation:{list,detail,export}`。无写入/删除接口。
- **stats 统计**：`func.count/avg` + `group_by`；今日边界用 `database.utils.timezone`（Asia/Shanghai 自然日转 UTC）；总量环比 = 全量 vs 截止上周日累计；今日环比 = 今日 vs 昨日；平均时长 = 当日均值、环比昨日均值（自然日窗口）；**意图分布按轮次表 `VoiceConsultationTurn.intent_type` 统计（join 会话表应用筛选，空意图轮次不计入）**，触发分布仍按会话表；分布 6/2 项 Python 侧补零 + 未知 code 兜底追加。
- **导出**：`modules/admin/exports/voice_consultation_export.py`，module_key `voice_consultation`，含 code→中文标签映射 + `enrich_fn` 填机器人名（2026-08-27 起不再导出会话级「意图类型」列）。

### 前端

- 视图 `views/voice-consultation/`（index + modules：stat-cards 渐变卡片、intent-bar-chart、trigger-pie-chart、session-search、session-detail-drawer 轮次对话列表）。
- 类型 `typings/api/voice-consultation.d.ts`（`Api.VoiceConsultation`）；API `service/api/voice-consultation.ts`。
- i18n：`route.voice-consultation*` + `page.manage.voiceConsultation.*`（zh-cn/en-us/app.d.ts 三处同步）。
- 路由：vite 插件重生成（`sa gen-route` CLI 是交互式的，用 `npx vite build` 触发生成即可），component 字符串 `layout.base$view.voice-consultation`。

### DB 迁移

- `0003_add_voice_consultation_tables.py`：建两张表 + 索引（session: robot_id/occurred_at/status/intent_type；turn: session_id）。**created_at 带 `server_default=sa.func.now()` 兜底外部写入漏传**。
- `0004_seed_voice_consultation_menu.py`：顶级 MENU `voice-consultation`（id 3000000000000120，component `layout.base$view.voice-consultation`，icon `mdi:microphone-message`，sort 7）+ 3 个 BUTTON（id 121/122/123）。downgrade 按 id 删除。

## 约束与备注

- **2026-08-27 变更**：会话级意图类型从查询参数（`VoiceConsultationSessionQueryParams.intent_type`）、响应字段（`VoiceConsultationSessionResponse.intent_type`）、详情抽屉、导出列、前端 typing/i18n（`intentTypeLabel`）全部移除；DB 列保留，外部写入约定不变；意图仅保留在轮次维度（详情抽屉每轮标签 + 意图分布柱状图按轮次统计）。
- **外部写入方对接要点**：`id` 为雪花主键无 DB 默认，外部必须自行生成唯一 BigInteger；`created_at` 已有 server_default 兜底但建议显式提供；`turn_count` 为冗余字段由外部维护；`occurred_at` 是业务时间（列表排序/筛选字段），区别于入库时间 `created_at`。
- **前端类型陷阱**：`Common.CommonRecord` 自带 `status: EnableStatus | null`（'1'/'2'），与业务 status 枚举冲突会把交叉类型折叠成 never —— `SessionRecord` 用 `Omit<Common.CommonRecord, 'status'> & {...}` 规避。
- **i18n 层级**：页面文案放 `page.manage.voiceConsultation.*`（manage 下，与 callLog 同级），不是 `page.voiceConsultation.*`。
- 环比语义：卡片统计（总量/今日/平均时长）均不随筛选；平均时长为当日口径、环比昨日（2026-08-26 由全量均值改为当日均值）；时间筛选只影响意图/触发分布图表。

## 记录日期

2026-08-19
