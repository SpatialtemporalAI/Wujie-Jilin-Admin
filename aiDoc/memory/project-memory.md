# 项目记忆索引

本文件是 `aiDoc/memory/` 的总入口。

## 长期记忆

- [MappedAsDataclass 模型 Optional 字段需 default=None](./long-term/mappedasdataclass-optional-field-default.md) — 否则 dataclass __init__ 把 Optional 字段当必填位置参数，实例化时报 missing、接口 500

## 业务需求记忆

- [2026-06-11 机器人配置迁移修复](./business/2026-06-11_robot-config-migration-fix.md) — 修复 robot_voice_config 存量表缺少 robot_id 导致语音配置接口 500
- [2026-06-11 人脸识别人像预览路径修复](./business/2026-06-11_face-photo-preview-path.md) — 避免持久化带 token 的完整预览 URL 导致 photo_url 超长 422
- [2026-06-11 人脸识别删除修复](./business/2026-06-11_face-delete-fix.md) — 修复删除配置时错误调用 soft_delete，并补齐移除人像清空字段
- [2026-06-11 人脸识别人像上传接口修复](./business/2026-06-11_face-upload-endpoint.md) — 新增机器人配置专用上传接口，避免上传人像 404
- [2026-06-11 机器人参数配置选择机器人布局调整](./business/2026-06-11_robot-config-select-layout.md) — 行走速度和电量报警阈值改为下拉选择机器人后读取配置
- [2026-06-11 地图编辑器右侧卡片与机器人总览](./business/2026-06-11_map-editor-right-panel-robot-overview.md) — 修复右侧卡片遮盖并新增机器人总览 tab
- [2026-06-11 地图编辑器机器人定位与绑定场景](./business/2026-06-11_map-editor-robot-location-binding.md) — 机器人总览列表支持定位与切换绑定场景
- [2026-06-11 场景地图 JSON 点位导入](./business/2026-06-11_scene-map-json-import.md) — 地图编辑器支持将 label/position JSON 导入为标注点
- [2026-06-11 机器人场景绑定可空与存量库缺列修复](./business/2026-06-11_robot-map-binding-nullable-fix.md) — robot.map_id 缺列自动补齐，未绑定场景不支持定位
- [2026-06-11 地图编辑器新增场景图片与扫图起始点](./business/2026-06-11_map-editor-create-scene-image-start-point.md) — 新增场景上传图片并按原图/网页显示尺寸缩放保存扫图起始点
- [2026-06-17 场景地图新增导航地图图片](./business/2026-06-17_scene-map-nav-image.md) — 异步将障碍物/禁区绘制到原图副本生成 nav_image_id
- [2026-06-17 机器人管理移除列表状态列](./business/2026-06-17_robot-manage-remove-status-column.md) — 去掉机器人管理表格中的状态显示列
- [2026-06-17 场景地图新增映射比例输入](./business/2026-06-17_scene-map-resolution-input.md) — 新增/编辑场景地图时填写 resolution，默认 1
- [2026-06-17 任务管理页面白色卡片背景调整](./business/2026-06-17_task-page-card-background.md) — 任务管理页增加白色卡片容器以修正 UI 样式偏差
- [2026-06-17 地图编辑器、机器人新增与任务管理修复](./business/2026-06-17_editor-robot-task-fixes.md) — 调整地图编辑器交互/默认值、机器人新增默认配置并修复任务页空白
- [2026-06-17 场景地图、任务列表与运行监控 UI 修复](./business/2026-06-17_scene-task-monitor-ui-fixes.md) — 修复图片预览、任务表格/禁用操作和运行监控地图布局
- [2026-06-17 任务新增编辑必填校验](./business/2026-06-17_task-form-required-validation.md) — 巡逻点位/动作和定时日期/开始时间提交前必填校验
- [2026-06-17 任务启用禁用按钮修复](./business/2026-06-17_task-toggle-enabled-fix.md) — 统一任务列表 enabled 状态转换，修复切换按钮无反应
- [2026-06-17 任务地图优先选择与点位删除联动](./business/2026-06-17_task-map-selection-and-point-cascade.md) — 任务先选地图、列表支持地图/机器人筛选，并联动删除任务点位
- [2026-06-17 任务场景筛选显示与地图编辑器场景名](./business/2026-06-17_task-scene-filters-and-map-editor-name.md) — 任务各列表补场景显示/筛选，地图编辑器显示当前场景名
- [2026-06-17 任务固化场景地图字段](./business/2026-06-17_task-map-id-fixed.md) — Task 新增 map_id，机器人改绑不再影响任务场景配置
- [2026-06-24 定时扫描调度任务并自动启动/恢复执行](./business/2026-06-24_task-schedule-scan.md) — 每分钟扫描 schedule_enabled+enabled 的任务，命中调度时间则恢复或新建执行
- [2026-06-24 场景地图主图上传接口独立权限化](./business/2026-06-24_scene-map-upload-image-endpoint.md) — 新增 /scene/map/upload-image 复用 scene:map:add/edit 权限；编辑器保存静默处理已软删 task
- [2026-06-24 机器人管理 gRPC 配置 + UI 隐藏 + 删除/权限修复](./business/2026-06-24_robot-manage-grpc-config-and-fixes.md) — robot 表加 grpc_config JSON + robot:manage:grpc_config 权限；隐藏状态按钮/搜索框；修删除外键报错；修编辑任务触发 scene:map:list
- [2026-06-25 登录后默认跳转权限列表第一个页面](./business/2026-06-25_login-redirect-first-permission.md) — RouteService 不再硬编码 home="home"，改为按菜单顺序取第一个叶子路由名作为首页
- [2026-06-25 机器人 gRPC 配置新增 ros 选项](./business/2026-06-25_robot-grpc-config-add-ros.md) — grpc_config JSON 在 agent / middleware 基础上扩展 ros 子对象，无 DDL、无新增权限
- [2026-06-25 参数配置 gRPC 调用从 robot.grpc_config 取地址](./business/2026-06-25_param-config-grpc-from-robot.md) — voice/speed/battery/face 4 类 RPC 按 RPC 类型分流到 grpc_config 的 agent/middleware；人脸走广播；不回退 settings
- [2026-06-26 任务选地图权限 + gRPC 重试去重](./business/2026-06-26_task-scene-map-list-and-grpc-retry-dedup.md) — scene_map list 接口 OR 加入 task:list；grpc 重试 save_pending 前按业务键取消旧 pending（face 按 face_id，其他按 robot_id）
- [2026-06-26 任务选地图后加载点位权限](./business/2026-06-26_task-scene-map-annotation-list-permission.md) — scene_map_annotation list 接口 OR 加入 task:list，修复编辑/选择地图后巡逻点位列表 403
- [2026-06-26 gRPC 重试 retry_count 不递增](./business/2026-06-26_grpc-retry-count-not-advancing.md) — _retry_one 加 30s 硬超时 + 三种失败路径统一推进 retry_count；retry_failed_pushes 任务 timeout 调到 1600s
- [2026-06-26 菜单本地图标类型不生效](./business/2026-06-26_menu-local-icon-type-persistence.md) — sys_menu 加 meta_icon_type 列；schema/前端 API 全栈透传 iconType，修复选「本地」保存后丢失
- [2026-06-26 任务执行 gRPC 推送补全](./business/2026-06-26_task-execution-grpc-push.md) — 新建 TaskConfigClient + task_pb2 path bridge；start/pause/resume/stop 4 类操作 commit 后下发 agent，失败仅日志不入重试
- [2026-06-29 机器人管理卡片按钮补齐权限控制](./business/2026-06-29_robot-manage-button-permissions.md) — 编辑/gRPC配置/状态/删除 4 个按钮按 robot:manage:edit/grpc_config/list/delete 隐藏
- [2026-06-29 阿里云人脸库管理模块](./business/2026-06-29_face-recognition-aliyun.md) — 新增 modules/face：facebody 人脸库增删查，密钥走 settings.FACE，UploadFile→viapi FileUtils→OSS→facebody
- [2026-06-29 菜单管理按钮权限补全 i18n](./business/2026-06-29_menu-button-permissions-i18n.md) — 全部按钮权限(menuType=3)补 route.* 中英文翻译(动作词)；8 个中文 scheduler 按钮经 0035 迁移改 ASCII 名，修复表格按钮行显示 route.xxx
- [2026-06-29 地图编辑器点位落障碍物拦截](./business/2026-06-29_map-editor-point-on-obstacle-guard.md) — 右键添加点位若落在 obstacle-* 上则拦截并提示「注意：点位不能设置在障碍物上！」
- [2026-06-29 菜单路径前缀继承/目录级联/移到根目录](./business/2026-06-29_menu-path-prefix-cascade.md) — path 与 name 解耦：路径=父级前缀+自身段；目录改路径后端级联后代 path；移到根目录自动裁路由名末段+补 layout 使其作为一级路由渲染
- [2026-06-29 移除本服务定时调度 + 启动改纯 gRPC](./business/2026-06-29_task-schedule-removed-and-start-grpc-only.md) — 删除每分钟扫描器；schedule_* 字段保留作外部调度程序契约；任务管理/OpenAPI 启动只下发 gRPC run_now，不再写 execution_record
- [2026-06-30 任务定时配置真正落库](./business/2026-06-30_task-schedule-fields-persist.md) — 前端 submitData 漏传 schedule_date/schedule_start_time（dayjs 时间戳↔ISO 转换）；后端 TaskResponseData 这两字段 Optional[str]→Optional[date]/[time]，修复落库后响应序列化 422
- [2026-06-30 创建机器人默认启用唤醒词小护小护](./business/2026-06-30_robot-default-wake-word.md) — RobotService.create 建 RobotVoiceConfig 默认 wake_word_enabled=True/wake_word=小护小护；默认常量集中到 model 模块，get_voice_config 兜底默认同步
- [2026-06-30 参数配置 gRPC target 调整](./business/2026-06-30_param-config-grpc-target-tweak.md) — 唤醒词测试 TestWakeWord + 电量阈值 NotifyBatteryThresholdChanged 的 target 由 middleware 改为 agent（config_client.py）
- [2026-06-30 地图编辑器显示机器人位置 + 修复定位](./business/2026-06-30_map-editor-robot-position.md) — 位置数据外部写入 DB 平台只读；新增 GET /robot/manage/map/{id}/robot-locations；画布渲染红色圆点机器人标记(纯视觉不落库/不导出)；extractRobotPoint 统一解析(location_info 优先,location 文本兜底)修复定位
- [2026-06-30 地图编辑器「扫图起始点」返回点与 start_point 解耦](./business/2026-06-30_map-editor-start-point-decouple-return-point.md) — 新增场景自动创建的「扫图起始点」返回点固定存为世界坐标 (0,0)，不再随 start_point 变化；start_point 仍必填、仍作坐标系原点
- [2026-06-30 地图编辑器删除地图后自动切换到第一个](./business/2026-06-30_map-editor-delete-auto-switch.md) — 删除当前选中地图后自动 loadMap 列表第一项，避免画布空载；删非当前地图不影响当前画布
- [2026-06-30 map.proto 新增 SwitchMap 切换机器人当前地图](./business/2026-06-30_map-switch-rpc.md) — MapService 新增 SwitchMap(id+version)，与广播地图 NotifyMapSaved 共用同一 gRPC 地址；接入切换地图接口 PUT /robot/manage/{id}/bind-map，绑定成功后下发、解绑不下发、失败仅日志
- [2026-07-01 任务点位动作列表可为空](./business/2026-07-01_task-point-actions-optional.md) — 添加/编辑任务新增点位时动作列表不再强制至少一个；addPoint 初始 actions=[]，删除动作去掉 >1 限制；后端本就支持空，仅前端表单调整
- [2026-07-01 任务绑定机器人与场景一致性提示](./business/2026-07-01_task-bind-robot-scene-tip.md) — 新增/编辑任务抽屉「任务类型」下方加 NAlert 警示：机器人不在任务绑定场景下任务无法执行，纯前端展示
- [2026-07-01 参数配置·人脸识别阿里云错误友好化解析](./business/2026-07-01_param-config-face-aliyun-error-parse.md) — face_service 新增错误码→中文提示映射 + _describe_aliyun_error 解析器，facebody/OSS 失败不再裸抛 Response 字典，前端 toast 显示「中文提示（错误码：XXX）」
- [2026-07-01 任务运控动作选项替换为新14项](./business/2026-07-01_task-action-options-replace.md) — 下拉换为 shake_hand/high_five/hug/high_wave/clap/face_wave/left_kiss/hands_up/x_ray/right_hand_up/reject/right_kiss/two_hand_kiss/no；详情抽屉保留旧值中文标签兼容历史快照；DB 无需迁移
- [2026-07-02 运行监控未绑定场景地图时不显示机器人点位](./business/2026-07-02_operation-monitor-hide-robot-point-without-map.md) — renderRobotMarker 加 `!mapData.value` 守卫，未绑定地图时不在空白画布画红点
- [2026-07-02 接口传参类型校验收紧](./business/2026-07-02_param-type-validation-tighten.md) — base.py 新增 `parse_optional_enum` 工厂；机器人/事件日志/执行记录/调度日志的 status、source、event_type 等查询字段补枚举校验；`RobotQueryParams.{model_id,map_id}`、`SceneMapQueryParams.group_id` 统一 `OptionalIntField`；前端 robot-operate-drawer 去掉 `undefined as unknown as number` 类型谎言
- [2026-07-02 任务运控动作下拉精简](./business/2026-07-02_task-action-options-trim.md) — 移除 击掌/拥抱/左手飞吻/右手飞吻/双手飞吻/动感光波 6 项，下拉保留 8 项；详情 actionLabel、TaskAction 类型、后端 schema 不动以兼容历史快照

- [2026-07-02 任务新增/编辑机器人改为单选](./business/2026-07-02_task-robot-single-select.md) — 接口层限制 robot_ids 长度必须为 1，前端选择器改为单选，数据库结构不变
- [2026-07-02 前端 CRUD 异常后仍弹成功提示修复](./business/2026-07-02_frontend-crud-error-success-toast.md) — 修正 user-operate-drawer 与 scene-map-detail-drawer 的错误处理，使用 `createFlatRequest` 返回的 `error` 字段判断，避免错误弹窗后再弹成功弹窗
- [2026-07-03 场景地图新增/编辑核心字段必填](./business/2026-07-03_scene-map-form-required-validation.md) — 地图管理与地图编辑器新增/编辑场景仅核心字段必填，状态与分组由后端默认值管理
- [2026-07-03 地图同步 gRPC 改走机器人 middleware 地址](./business/2026-07-03_map-grpc-to-middleware.md) — NotifyMapSaved 按 Robot.map_id 广播 + SwitchMap 按 robot_id 改走 robot.grpc_config.middleware；SearchMaps 仍走全局 MAP_SERVICE_ADDR；参数配置 gRPC 不变
- [2026-07-03 运行监控速度按小数点后一位判断移动](./business/2026-07-03_operation-monitor-speed-round-one-decimal.md) — robot-status-card getSpeedLabel 改为先 `Math.round(speed*10)/10` 再 >0，与显示 toFixed(1) 对齐，过滤传感器微小波动误判
- [2026-07-03 OpenAPI 导航补全 dedicated gRPC](./business/2026-07-03_openapi-nav-grpc.md) — 新增 NavigationService(NavigateToPoint/Route)；OpenAPI goto_point/navigate_route 不再建临时 Task，直接下发 robot.agent；speak 仍复用 TestTTSConfig，未新增 Speak RPC
- [2026-07-06 日志管理三页面导出 Excel](./business/2026-07-06_log-export-excel.md) — 复用异步导出任务体系；后端注册 login_log/robot_event_log 导出（operation_log 已有）+ 前端首次接入：顶栏「下载箱」图标（仿通知中心 Popover）+ 登录/操作/机器人事件日志三页面导出按钮
- [2026-07-06 地图编辑器删除点位按任务关联决定确认](./business/2026-07-06_map-editor-point-delete-task-confirm.md) — 编辑器数据接口回填 annotation.task_count；前端删除点位仅在 task_count>0 时弹窗，否则直接删除；点位列表项去掉误导性常驻 Popconfirm
- [2026-07-06 角色名称与描述长度限制](./business/2026-07-06_role-name-max-length-20.md) — 后端 SysRoleCreate/Update name max_length 100→20、desc 加 max_length=200；前端 role-operate-drawer 名称/描述 NInput 加 maxlength+show-count
- [2026-07-06 跨模块下拉改调 /all 轻量接口](./business/2026-07-06_cross-module-dropdown-all-endpoint.md) — 新增 GET /robot/manage/all、GET /scene/group/all（仅登录、返回 SimpleResponse）；前端 6 处下拉（任务/商户/日志/场景地图搜索）由 list 改调 /all，根治跨模块下拉权限不足
- [2026-07-06 校验错误提示词去中英文混合](./business/2026-07-06_validation-error-message-pure-chinese.md) — errors_handler 用字段 description 反射指代字段（无描述回退「该参数」），消除 page_size必须为整数 这类混合；PYDANTIC_ERROR_ZH 扩充到约 90 项
- [2026-07-07 修复跨权限调用 robot:manage:list 接口](./business/2026-07-07_cross-permission-robot-list-callers.md) — 5 处下拉（地图编辑器总览/运营监控/参数配置 3 tab）由 /list 改调 /all；robot-locations 端点叠加 scene:map-editor:list（只读对齐 list，bind-map 写仍用 edit）
- [2026-07-07 用户新增·昵称改为非必填](./business/2026-07-07_user-create-nickname-optional.md) — SysUserCreate.nickname 由必填改 Optional（与 Update 对齐）；前端 rules 本就不含 nickname，根因是后端空串触发全局非空校验
- [2026-07-07 分页参数脏值防御性收敛 + OptionalIntField 错误中文化](./business/2026-07-07_pagination-dirty-value-coerce.md) — page/page_size 收到空串/"null"/"NaN" 等脏值不再 422，收敛到默认值；robot_id/map_id 等非数字字符串提示由英文 invalid literal 改中文「必须为整数」
- [2026-07-07 修复分页 count 恒返回 1](./business/2026-07-07_pagination-count-returns-1.md) — SA 2.0 with_only_columns 默认丢弃实体派生 FROM，纯实体查询页 count 退化为无 FROM 的 SELECT count(*)（PG 恒返回 1）；3 处加 maintain_column_froms=True（共享 get_paginated_results + 场景地图/分组）
- [2026-07-07 导出任务卡死修复](./business/2026-07-07_export-task-stuck-recover-and-timeout.md) — asyncio.create_task 在 gunicorn worker 回收时丢失致任务永卡 pending；新增两个每分钟定时任务（兜底补生成 + 超时失效），_execute_task 改原子领取防多 worker 重复；状态同步保留轮询（WebSocket 多 worker 推送会丢）
- [2026-07-07 高频轮询接口不写操作日志](./business/2026-07-07_operation-log-skip-polling-endpoints.md) — operation_log_middleware 新增 WHITELIST_SUFFIXES 后缀匹配，排除 robot-locations/status/latest/export/task/list 三个高频轮询接口（前缀匹配会误伤增删改）
- [2026-07-07 禁用用户不允许登录 + 禁用角色权限](./business/2026-07-07_disable-user-login-and-role-permission.md) — login/current_user 加 user.status 校验 + 新增 USER_DISABLED(10013)；禁用角色核心已实现（菜单树/权限码校验过滤 role.status），未改动
- [2026-07-07 导出任务弹窗样式优化 + 列表页](./business/2026-07-07_export-center-style-and-list-page.md) — 弹窗状态Tag移标题旁/下载改图标放右侧仅completed；新增 views/log/export-task 列表页(不进菜单)+「查看全部」入口；后端 list 加 status 筛选；顺带修 pre-existing map-editor→scene_map-editor + 放宽 I18nRouteKey(typecheck 全通过)
- [2026-07-07 地图保存/切换 gRPC 增加 agent 端推送](./business/2026-07-07_map-grpc-agent-push.md) — NotifyMapSaved 广播 + SwitchMap 单发由「只推 middleware」改为「middleware + agent 双推」，复用同一 MapService RPC；client.py / addr_provider.py / proto / 前端零改动，纯调用方路由扩展；agent 端需部署 MapService
- [2026-07-07 历史任务列表按结束时间倒序](./business/2026-07-07_task-history-sort-by-finish-time.md) — build_history_query 排序由 id.desc() 改为 finish_time.desc().nulls_last()；仅历史任务，活跃任务列表不动；前端零改动
- [2026-07-07 保存地图默认推送所有机器人](./business/2026-07-07_map-save-push-all-robots.md) — NotifyMapSaved 广播去掉 Robot.map_id 过滤（find_addrs_by_target_and_map → find_addrs_by_target），保存任一地图即向全部启用 middleware/agent 的机器人下发；SwitchMap 单发不动
- [2026-07-07 任务执行/历史列表与执行详情补齐即时任务类型](./business/2026-07-07_task-type-instant-execution-views.md) — 承接 0706：task-history-tab / task-execution-tab 表格 NTag + task-detail-drawer 文本展示补齐 instant=即时(warning)；统一 taskTypeLabel + taskTypeTagType 查表
- [2026-07-07 执行详情触发源补充语音输入/手动恢复](./business/2026-07-07_task-execution-source-label-extend.md) — task-detail-drawer sourceLabelMap 加 text_input=语音输入/resume=手动恢复；仅详情展示，表格不加列；后端枚举未动(agent 写库不经 Literal)
- [2026-07-07 播报任务隐藏场景地图并支持多选机器人](./business/2026-07-07_task-broadcast-no-map-and-multi-robot.md) — 承接 0702：播报任务隐藏场景地图输入框/提示+机器人改多选；巡逻不动；后端 robot_ids 校验改按 task_type 区分（patrol 单选 / broadcast 多选）
- [2026-07-08 实时下发接口增加机器人在线前置校验](./business/2026-07-08_robot-online-check-before-dispatch.md) — 唤醒词测试/语音合成测试/启动任务下发前经 `RobotService.ensure_robots_online` 校验 `Robot.status==online`，离线抛 ConflictError「机器人 X 不在线」由前端 onError 自动 toast；三处复用同一 helper，前端零改动
- [2026-07-10 运行监控实时视频接入 LiveKit](./business/2026-07-10_operation-monitor-livekit-video.md) — 运行监控页视频监控 Tab 通过 LiveKit 实时显示机器人摄像头，Redis 观众计数保证多用户共享时摄像头只在最后一人离开时关闭

## 维护说明

- 新增记忆时，在对应目录创建 Markdown 文件，并在此索引中添加条目
- 过时的记忆应及时清理
- 记忆文件应包含日期标记，便于判断时效性
