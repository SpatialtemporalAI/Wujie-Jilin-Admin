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
- [2026-06-25 登录后跳转权限列表第一个业务页面](./2026-06-25_login-redirect-first-permission.md) — 后端 `_find_first_leaf_route_name` 取第一个 `view.` 叶子作 `home` 并跳过 `home` 仪表盘；前端 `redirectFromLogin` 改为**按路由名跳转**第一个业务菜单（绕开静态 routeMap），根治「home 无权限 → 404」
- [2026-06-26 任务定义变更 gRPC 推送](./2026-06-26_task-definition-grpc-push.md) — 任务列表新增/编辑/删除/启用/禁用时 broadcast operation=create/edit/delete/enable/disable 到关联 robot_ids；复用 TaskConfigClient，不接重试队列
- [2026-06-26 任务运控动作选项更新 & 允许点位动作为空](./2026-06-26_task-action-options-update.md) — 动作列表可为空（min_length=1 → default_factory=list）；下拉换为 shake_hands/wave/left_hand/right_hand/bend_no_hands/bend_with_hands/no；新增动作项默认 no；详情抽屉保留老值兼容标签
- [2026-06-26 删除废弃 task_execution 表 + JSON 字段补类型注解](./2026-06-26_task-execution-cleanup-and-json-annotation.md) — 删 task_execution ORM/service/endpoint/schema/前端死代码 + 新建 0032 drop 迁移；task_execution_record 的 task_definition/progress 字段注释指向 Pydantic 类（文档作用，不加运行时校验）
- [2026-06-29 商户管理 + 商户开放 API](./2026-06-29_merchant-openapi.md) — 新建 merchant/merchant_robot 表 + HMAC 签名开放 API（goto_point/navigate_route/execute_task/暂停/恢复/停止/speak），复用任务管线与 gRPC；api_secret Fernet 可逆加密
- [2026-06-29 菜单管理按钮权限补全 i18n](./2026-06-29_menu-button-permissions-i18n.md) — 全部按钮权限(menuType=3)补 route.* 中英文翻译(动作词)；8 个中文 scheduler 按钮经 0035 迁移改 ASCII 名，修复表格按钮行显示 route.xxx
- [2026-06-29 菜单路径前缀继承/目录级联/移到根目录](./2026-06-29_menu-path-prefix-cascade.md) — path 与 name 解耦：路径=父级前缀+自身段；目录改路径后端级联后代 path；移到根目录自动裁路由名末段+补 layout 使其作为一级路由渲染
- [2026-06-29 移除本服务定时调度 + 启动任务改为纯 gRPC](./2026-06-29_task-schedule-removed-and-start-grpc-only.md) — 删 scan_scheduled_tasks 扫描器 + 0037 软删除调度行（定时调度移交外部程序，schedule_* 字段保留）；任务管理与 OpenAPI 的启动改为只下发 gRPC run_now，不再写 task_execution_record
- [2026-06-30 参数配置·人脸识别改为直连阿里云 facebody](./2026-06-30_param-config-face-aliyun-direct.md) — face 增删改不再走 gRPC 广播，改直连 FaceService 注册到人脸库 lvya；新增 entity_id/face_id 列（0038）；注册失败回滚本地，换图替换、删除 best-effort
- [2026-06-30 地图编辑器「扫图起始点」返回点与 start_point 解耦](./2026-06-30_map-editor-start-point-decouple-return-point.md) — 新增场景自动创建的「扫图起始点」返回点固定存为世界坐标 (0,0)，不再随 start_point 变化；start_point 仍必填、仍作坐标系原点
- [2026-06-30 地图编辑器删除地图后自动切换到第一个](./2026-06-30_map-editor-delete-auto-switch.md) — 删除当前选中地图后自动 loadMap 列表第一项，避免画布空载；删非当前地图不影响当前画布
- [2026-07-01 删除机器人清理任务关联](./2026-07-01_delete-robot-cleanup-task-association.md) — delete robot 时物理删除 task_robot 关联表中该 robot 的全部关联（从关联任务列表移除），避免孤儿关联；robot 软删除不触发 ondelete=CASCADE，不发 gRPC
- [2026-07-01 运行监控地图同步地图编辑器效果](./2026-07-01_operation-monitor-map-sync-editor.md) — operation-monitor 地图补左上角图例 + 右上角竖向滑块缩放（对数刻度）+ 点位角度方向箭头（annotation 改三个独立 fabric 对象，复用编辑器 getAnnotationArrowTransform）；机器人标记由蓝改红与图例对齐；滚轮缩放改用画布相对坐标 offsetX/Y（编辑器同改）；点位/机器人标记缩放时保持固定屏幕大小（applyMarkerZoom 反向缩放 1/zoom，位置仍随地图）
- [2026-07-01 参数配置·人脸识别阿里云错误友好化解析](./2026-07-01_param-config-face-aliyun-error-parse.md) — face_service 新增错误码→中文提示映射 + _describe_aliyun_error 解析器，facebody/OSS 失败不再裸抛 Response 字典，前端 toast 显示「中文提示（错误码：XXX）」
- [2026-07-01 参数配置·人脸识别编辑修复](./2026-07-01_param-config-face-edit-no-photo.md) — 编辑按钮点击后滚动回表单消除「无反应」；编辑态人像改只读预览不可改图，仅改名称/播报，后端 photo_changed 判定自动跳过换图
- [2026-07-01 任务运控动作选项替换为新14项](./2026-07-01_task-action-options-replace.md) — 下拉换为 shake_hand/high_five/hug/high_wave/clap/face_wave/left_kiss/hands_up/x_ray/right_hand_up/reject/right_kiss/two_hand_kiss/no；详情抽屉保留旧值中文标签兼容历史快照；DB 无需迁移
- [2026-07-02 地图编辑器新增场景上传 ROS yaml 解析分辨率与起始点](./2026-07-02_map-editor-create-scene-yaml-config-parse.md) — 新增场景时扫图起始点/分辨率输入框禁用，改为上传 yaml 配置文件；新增独立解析接口 POST /scene/map-editor/parse-map-config（resolution + origin[0:2]），不改原 add 接口；requirements 显式加 pyyaml
- [2026-07-02 机器人事件日志挂到日志管理菜单](./2026-07-02_robot-event-log-menu.md) — 功能全栈已就绪，唯一缺口是 sys_menu 种子；新增迁移 0039 在日志管理目录下插入 log_robot-log 菜单 + list/delete 按钮（permission 对齐接口 robot:monitor:list / robot:event-log:delete）
- [2026-07-02 编辑扫图起始点时按差值平移子元素](./2026-07-02_map-editor-edit-start-point-offset-children.md) — SceneMapService.update 检测 start_point 变化时，同事务平移标注/物体/路径坐标以保持世界坐标(米)不变（机器人不动）；通式兼容 resolution 同变；start_point 变化也触发 nav_image 重建
- [2026-07-02 接口传参类型校验收紧](./2026-07-02_param-type-validation-tighten.md) — base.py 新增 `parse_optional_enum` 工厂；机器人/事件日志/执行记录/调度日志的 status、source、event_type 等查询字段补枚举校验；`RobotQueryParams.{model_id,map_id}`、`SceneMapQueryParams.group_id` 统一 `OptionalIntField`；前端 robot-operate-drawer 去掉 `undefined as unknown as number` 类型谎言
- [2026-07-02 任务运控动作下拉精简](./2026-07-02_task-action-options-trim.md) — 移除 击掌/拥抱/左手飞吻/右手飞吻/双手飞吻/动感光波 6 项，下拉保留 8 项；详情 actionLabel、TaskAction 类型、后端 schema 不动以兼容历史快照
- [2026-07-02 前端 CRUD 异常后仍弹成功提示修复](./2026-07-02_frontend-crud-error-success-toast.md) — 修正 user-operate-drawer 与 scene-map-detail-drawer 的错误处理，使用 `createFlatRequest` 返回的 `error` 字段判断，避免错误弹窗后再弹成功弹窗
- [2026-07-03 地图同步 gRPC 改走机器人 middleware 地址](./2026-07-03_map-grpc-to-middleware.md) — NotifyMapSaved 按 Robot.map_id 广播 + SwitchMap 按 robot_id 改走 robot.grpc_config.middleware；SearchMaps 仍走全局 MAP_SERVICE_ADDR；参数配置 gRPC 不变
- [2026-07-03 运行监控速度按小数点后一位判断移动](./2026-07-03_operation-monitor-speed-round-one-decimal.md) — robot-status-card getSpeedLabel 改为先 `Math.round(speed*10)/10` 再 >0，与显示 toFixed(1) 对齐，过滤传感器微小波动误判
- [2026-07-03 角色新增重名校验](./2026-07-03_role-create-duplicate-name-check.md) — `RoleService.create_role` 创建前查同名角色，存在则抛 `ConflictError(msg="角色名称已存在")`，HTTP 409 经前端 onError 自动 toast，无需改前端
- [2026-07-03 参数配置·人脸识别TTS 人像上传限制（5MB+格式+分辨率+说明）](./2026-07-03_param-config-face-photo-size-limit.md) — 对齐阿里云 facebody：前后端各校验 JPG/JPEG/PNG、≤5MB、分辨率 32×32~4096×4096；人脸占比 64×64 由 facebody 校验；人像输入框右侧加 5 条说明
- [2026-07-06 日志管理三页面导出 Excel](./2026-07-06_log-export-excel.md) — 复用异步导出任务体系；后端注册 login_log/robot_event_log 导出（operation_log 已有）+ 前端首次接入：顶栏「下载箱」图标（仿通知中心 Popover）+ 登录/操作/机器人事件日志三页面导出按钮
- [2026-07-06 全局必填字段非空校验 + 校验信息中文化](./2026-07-06_global-required-validation.md) — BaseEntity 全局 validator 统一必填非空（str 过滤纯空格/集合拒空/自动 trim）+ 校验失败信息中文化；响应类经 BaseRespEntity 或 _skip ClassVar 跳过；约 18 个 BaseModel 请求体迁 BaseReqEntity、约 40 个 BaseEntity 请求类零改动覆盖
- [2026-07-06 跨模块下拉改调 /all 轻量接口](./2026-07-06_cross-module-dropdown-all-endpoint.md) — 新增 GET /robot/manage/all、GET /scene/group/all（仅登录、返回 SimpleResponse）；前端 6 处下拉（任务/商户/日志/场景地图搜索）由 list 改调 /all，根治跨模块下拉权限不足
- [2026-07-06 任务类型新增「即时」(instant)](./2026-07-06_task-type-instant.md) — 任务列表筛选下拉与表格列新增 instant（即时）；TaskType 联合类型补 'instant'，NTag 颜色改查表映射；不动新增/编辑抽屉
- [2026-07-06 视频监控 gRPC 启停控制（对接 middleware）](./2026-07-06_video-monitoring-grpc-control.md) — 新增 config/video.proto（单一 RPC NotifyVideoMonitoringChanged(robot_id, enabled)）+ VideoMonitoringClient（走 middleware）+ POST /robot/config/video-monitoring/{robot_id}；实时控制 fire-and-forget，不入重试不落库；前端 API + 类型
- [2026-07-06 商户开放 API 接口补类型校验](./2026-07-06_openapi-param-validation.md) — openapi schema 补 task_type/status 枚举（parse_optional_enum）、speed(0.5–2.0)/volume(0–100) 范围、map_id 改 OptionalIntField；接入文档错误码表加 422；voice 枚举与 ID ge=1 不加
- [2026-07-07 修复跨权限调用 robot:manage:list 接口](./2026-07-07_cross-permission-robot-list-callers.md) — 5 处下拉（地图编辑器总览/运营监控/参数配置 3 tab）由 /list 改调 /all；robot-locations 端点叠加 scene:map-editor:list（只读对齐 list，bind-map 写仍用 edit）
- [2026-07-07 用户新增·昵称改为非必填](./2026-07-07_user-create-nickname-optional.md) — SysUserCreate.nickname 由必填改 Optional（与 Update 对齐）；前端 rules 本就不含 nickname，根因是后端空串触发全局非空校验
- [2026-07-07 分页参数脏值防御性收敛 + OptionalIntField 错误中文化](./2026-07-07_pagination-dirty-value-coerce.md) — page/page_size 收到空串/"null"/"NaN" 等脏值不再 422，收敛到默认值；robot_id/map_id 等非数字字符串提示由英文 invalid literal 改中文「必须为整数」。BeforeValidator 仅 BaseModel 字段生效（FastAPI 限制）
- [2026-07-07 修复分页 count 恒返回 1](./2026-07-07_pagination-count-returns-1.md) — SA 2.0 with_only_columns 默认丢弃实体派生 FROM，纯实体查询页 count 退化为无 FROM 的 SELECT count(*)（PG 恒返回 1）；3 处加 maintain_column_froms=True（共享 get_paginated_results + 场景地图/分组）
- [2026-07-07 导出任务卡死修复](./2026-07-07_export-task-stuck-recover-and-timeout.md) — asyncio.create_task 在 gunicorn worker 回收时丢失致任务永卡 pending；新增两个每分钟定时任务（兜底补生成 pending>90s + 超时失效 processing>600s），_execute_task 改原子领取防多 worker 重复；状态同步经评估保留轮询（FastAPIConnectionManager 进程内存在 4 worker 下推送会丢，WebSocket 需额外 Redis pub/sub 桥接，低频导出不划算）
- [2026-07-07 高频轮询接口不写操作日志](./2026-07-07_operation-log-skip-polling-endpoints.md) — operation_log_middleware 原仅 WHITELIST_PREFIXES 前缀匹配；新增 WHITELIST_SUFFIXES 后缀匹配排除 robot-locations / status/latest / export/task/list 三个高频轮询接口（带动态路径参数，前缀匹配会误伤同前缀增删改）
- [2026-07-07 禁用用户不允许登录 + 禁用角色权限](./2026-07-07_disable-user-login-and-role-permission.md) — login_by_password/current_user 加 user.status 校验（登录 CustomError 提示 + current_user TokenError 401 踢下线，受 30s USER 缓存影响）；新增 USER_DISABLED(10013)；禁用角色经核实核心已实现（菜单树/权限码校验都过滤 role.status），未改动
- [2026-07-07 地图保存/切换 gRPC 增加 agent 端推送](./2026-07-07_map-grpc-agent-push.md) — NotifyMapSaved 广播 + SwitchMap 单发由「只推 middleware」改为「middleware + agent 双推」，复用同一 MapService RPC；client.py / addr_provider.py / proto / 前端零改动，纯调用方路由扩展；agent 端需部署 MapService
- [2026-07-07 保存地图默认推送所有机器人](./2026-07-07_map-save-push-all-robots.md) — NotifyMapSaved 广播去掉 Robot.map_id 过滤，由 find_addrs_by_target_and_map 改为 find_addrs_by_target，保存任一地图即向全部启用 middleware/agent 的机器人下发；SwitchMap 单发不在范围
- [2026-07-08 实时下发接口增加机器人在线前置校验](./2026-07-08_robot-online-check-before-dispatch.md) — 唤醒词测试/语音合成测试/启动任务下发前经 `RobotService.ensure_robots_online` 校验 `Robot.status==online`，离线抛 ConflictError「机器人 X 不在线」由前端 onError 自动 toast；三处复用同一 helper，前端零改动
- [2026-07-08 GRPC 同步：定时重试在线前置 + 同类消息覆盖](./2026-07-08_grpc-retry-online-first-and-overwrite.md) — 定时重试改为先检测在线（离线延后重扫不耗退避）；覆盖取消上移到推送入口（修复新成功后旧值补推）；保存地图/切换地图纳入 grpc_retry_task（覆盖键分别含 map_id / 仅 robot_id）；新增 RetryCallResult + MapRetryHelper，grpc_retry_task 加可空 map_id 列；openapi 不变
- [2026-07-08 开放商户目录 + 商户 OpenAPI 调用日志](./2026-07-08_open-merchant-call-log.md) — 新建「开放商户」一级目录，商户管理移入其下 + 新增「调用日志」；中间件自动捕获 /openapi/v1/* 调用落库（api_key 掩码、签名/密钥绝不入库）；0040 建表 + 0041 菜单迁移（manage_merchant → open-merchant_merchant）；前端视图目录重构 + gen-route + i18n + api/typings
- [2026-07-13 gRPC 重试任务置 dead 时 next_retry_at 不能置 NULL](./2026-07-13_grpc-retry-dead-next-retry-not-null.md) — `_advance_fields` dead 分支删 `next_retry_at = None`（列为 NOT NULL，置空致 commit 抛 IntegrityError、任务每分钟卡死）；dead 行靠 status 过滤排除，无需改 schema/迁移
