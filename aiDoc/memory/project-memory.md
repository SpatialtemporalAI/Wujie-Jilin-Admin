# 项目记忆索引

本文件是 `aiDoc/memory/` 的总入口。

## 长期记忆

暂无。

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

## 维护说明

- 新增记忆时，在对应目录创建 Markdown 文件，并在此索引中添加条目
- 过时的记忆应及时清理
- 记忆文件应包含日期标记，便于判断时效性
