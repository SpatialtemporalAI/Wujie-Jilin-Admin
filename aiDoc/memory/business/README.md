# 业务需求记忆

存放每次用户提出的业务需求记录。

## 规则

- 用户提出业务需求时，**必须**新增或更新一条记录
- 使用 `TEMPLATE.md` 作为新记录的模板
- 记录完成后在 `project-memory.md` 中更新索引

## 需求索引

- [2026-05-24 API 限流 / IP 黑名单](./2026-05-24_rate_limit_blacklist.md) — Redis 多维度限流 + DB 持久化 IP 黑名单 + 自动拉黑
- [2026-05-31 多租户插件](./2026-05-31_multi_tenant_plugin.md) — 可选多租户插件，行级隔离，JWT 识别租户
- [2026-05-31 租户表隔离与权限设计](./2026-05-31_tenant_table_permissions.md) — strict/optional/全局三级隔离 + 权限分级
- [2026-06-01 租户 JWT 配置 + 登录自动选择租户](./2026-06-01_tenant_jwt_config_and_auto_select.md) — 混合模式 JWT 签名 + 登录自动选租户 + Redis/DB 双写
- [2026-06-01 插件安装自动更新 PLUGINS__ENABLED](./2026-06-01_auto_update_plugins_enabled.md) — 安装/卸载插件时自动更新 .env 中的启用列表
- [2026-06-03 数据库模块迁移](./2026-06-03_database_migration.md) — ORM 模型、连接管理、工具函数统一迁移到 database/ 包
- [2026-06-03 字典通用组件](./2026-06-03_dict_components.md) — useDict composable + DictSelect/DictTag/DictText 通用组件 + gender 种子数据
- [2026-06-09 任务管理](./2026-06-09_task-management.md) — 机器人巡逻/播报任务管理，含任务配置、执行控制、历史记录
- [2026-06-11 机器人配置迁移修复](./2026-06-11_robot-config-migration-fix.md) — 修复 robot_voice_config 存量表缺少 robot_id 导致语音配置接口 500
- [2026-06-11 人脸识别人像预览路径修复](./2026-06-11_face-photo-preview-path.md) — 避免持久化带 token 的完整预览 URL 导致 photo_url 超长 422
- [2026-06-11 人脸识别删除修复](./2026-06-11_face-delete-fix.md) — 修复删除配置时错误调用 soft_delete，并补齐移除人像清空字段
- [2026-06-11 人脸识别人像上传接口修复](./2026-06-11_face-upload-endpoint.md) — 新增机器人配置专用上传接口，避免上传人像 404
- [2026-06-11 机器人参数配置选择机器人布局调整](./2026-06-11_robot-config-select-layout.md) — 行走速度和电量报警阈值改为下拉选择机器人后读取配置
- [2026-06-11 地图编辑器右侧卡片与机器人总览](./2026-06-11_map-editor-right-panel-robot-overview.md) — 修复右侧卡片遮盖并新增机器人总览 tab
- [2026-06-11 地图编辑器机器人定位与绑定场景](./2026-06-11_map-editor-robot-location-binding.md) — 机器人总览列表支持定位与切换绑定场景
- [2026-06-11 场景地图 JSON 点位导入](./2026-06-11_scene-map-json-import.md) — 地图编辑器支持将 label/position JSON 导入为标注点
- [2026-06-11 机器人场景绑定可空与存量库缺列修复](./2026-06-11_robot-map-binding-nullable-fix.md) — robot.map_id 缺列自动补齐，未绑定场景不支持定位
- [2026-06-11 地图编辑器新增场景图片与扫图起始点](./2026-06-11_map-editor-create-scene-image-start-point.md) — 新增场景上传图片并按原图/网页显示尺寸缩放保存扫图起始点
- [2026-06-17 场景地图新增导航地图图片](./2026-06-17_scene-map-nav-image.md) — 异步将障碍物/禁区绘制到原图副本生成 nav_image_id
- [2026-06-18 NotifyMapSaved image_url HMAC 签名 URL](./2026-06-18_notify-map-saved-image-url-internal-token.md) — preview 端点改为 HMAC 签名 URL（?expires=&sig=），密钥不出后端，有时效
- [2026-06-18 运行监控页面滚动 + 登录后底部栏隐藏](./2026-06-18_operation-monitor-scroll-and-footer-hidden.md) — operation-monitor 改为纵向滚动，主题 footer.visible 默认 false 并通过 overrideThemeSettings 强制覆盖老用户缓存
- [2026-06-18 前后端生产环境启动脚本](./2026-06-18_prod-startup-scripts.md) — 前端 `pnpm start:prod` 串联 build+preview；后端 `backend/start_prod.sh` 用 gunicorn+uvicorn worker 启动并设 ENVIR=prod
- [2026-06-19 地图编辑器电子围栏](./2026-06-19_map-editor-electronic-fence.md) — 右键新增电子围栏（红色矩形），多个围栏 OR 语义，后端 nav_image 反向涂黑围栏外区域
- [2026-06-22 任务管理移除播报次数配置](./2026-06-22_task-remove-broadcast-count.md) — 播报类型任务只保留播报文本，后端字段保留兼容历史数据
- [2026-06-23 settings 权限/滚动 + 任务多动作 + 独立执行记录表](./2026-06-23_settings-and-task-multi-action-execution-record.md) — settings 统一 robot:config:edit、表单可折叠、点位多动作(JSON)、新建 task_execution_record 表存储快照
- [2026-06-24 定时扫描调度任务并自动启动/恢复执行](./2026-06-24_task-schedule-scan.md) — 每分钟扫描 schedule_enabled+enabled 的任务，命中 schedule_start_time+repeat_cycle/date 则恢复 paused 或新建执行（source=platform_schedule）
- [2026-06-24 voice.proto 拆分为唤醒词 + 语音合成两个 RPC](./2026-06-24_voice-proto-split-wakeword-tts.md) — `NotifyVoiceConfigChanged` 拆为 `NotifyWakeWordChanged` + `NotifyTTSConfigChanged`，message 与字段按职责分离
- [2026-06-24 语音合成语速参数改为 0.5-2 浮点 + slider 样式优化](./2026-06-24_tts-speed-float-range.md) — tts_speed 全栈 int(0-100)→float(0.5-2.0, step 0.1)，含 DB 迁移与 voice_pb2 二进制手改
- [2026-06-24 唤醒词测试显示模拟回应话术 + proto 新增测试 RPC](./2026-06-24_voice-test-wakeword-response.md) — 点击测试在按钮右侧显示「<唤醒词>在呢，有什么可以帮您？」；voice.proto 新增 TestWakeWord / TestTTSConfig 两个 RPC
- [2026-06-24 参数配置页面接入 gRPC client 骨架](./2026-06-24_param-config-grpc-scaffold.md) — 4 Tab 所有保存/测试/增删改按钮 DB commit 后调对应 Notify/Test RPC；通用 _dispatch 调度内核 + 4 业务 Client + ConfigServiceAddrProvider 抽象（为数据库读取预留）
- [2026-06-25 gRPC 推送失败持久化重试队列](./2026-06-25_grpc-push-retry-queue.md) — 新建 grpc_retry_task 表 + 调度任务每分钟扫描重试（指数退避 60s/120s/240s，3 次后 dead）；前端"绿色 success + 备注"区分 synced/pending_retry；测试按钮失败直接 fail 不入队
- [2026-06-26 任务定义变更 gRPC 推送](./2026-06-26_task-definition-grpc-push.md) — 任务列表新增/编辑/删除/启用/禁用时 broadcast operation=create/edit/delete/enable/disable 到关联 robot_ids；复用 TaskConfigClient，不接重试队列
