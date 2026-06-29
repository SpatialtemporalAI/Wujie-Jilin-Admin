# 阿里云人脸库管理模块（facebody）

## 需求描述

将仓库根目录独立脚本 `face_recognition.py`（密钥从 `aliyun.env` 读取、CLI 形态）改造为后端标准模块，
对外提供带 JWT 鉴权的 REST 接口，管理阿里云人脸库（人脸体 Facebody 服务）：
建库 / 列库 / 增删实体 / 增删人脸图片 / 搜索 / 检测。密钥改为从项目 `settings`（`.env`）读取。

## 状态

已完成（后端单栈）。`.env.dev` 中 `FACE__ACCESS_KEY_*` 为占位值，需填真实密钥。
菜单与按钮权限已通过 alembic 迁移 `0036_seed_face_menu` 种子化（菜单 manage_face 挂在 manage 目录下、
暂 `meta_hidden=True` 因无前端页面；8 个按钮权限码 face:*）。迁移需 `alembic upgrade head` 生效。

## 涉及范围

### 后端

- 新模块 `backend/modules/face/`（endpoints / services / schemas / router）
- `core/config` 新增 `FACE` 配置：`FaceRecognitionModel`（ENABLED / ACCESS_KEY_ID /
  ACCESS_KEY_SECRET / ENDPOINT / REGION_ID / DEFAULT_DB_NAME）
- 依赖新增：`alibabacloud-facebody20191230`、`alibabacloud-tea-openapi`、
  `alibabacloud-tea-util`、`viapi-utils`（本地文件传 OSS）、
  `aliyun-python-sdk-core`、`aliyun-python-sdk-viapiutils`、`oss2`
  （viapi-utils 未声明对 legacy SDK / oss2 的依赖，需显式声明）
- `backend/main.py` 注册 `face_router`

### 前端

- 页面 `frontend/src/views/manage/face/`：`index.vue`（NTabs 三页签：人脸库管理 / 搜索 / 检测）
  + `modules/face-entity-faces-drawer.vue`（实体下人脸图片：列表/删除/上传入库）
  + `modules/face-search.vue`、`modules/face-detect.vue`
- 人脸库管理 Tab：人脸库下拉 + 新建库 + 实体分页表格（`useNaivePaginatedTable`，`immediate:false`，选库后才加载）
  + 行内"查看人脸/删除"；表头新增实体
- API `frontend/src/service/api/face.ts`、类型 `frontend/src/typings/api/face.d.ts`（namespace `Api.Face`），barrel 已导出
- i18n：`route.manage_face` + `route.face_*`（按钮权限）+ `page.manage.face.*`（页内文案）；
  Schema 手写在 `src/typings/app.d.ts` 的 `Schema.page.manage.face`（需与 locale 同步增删 key）
- 路由由 `pnpm gen-route` 自动生成（`manage_face` → `src/views/manage/face/index.vue`），勿手改 `router/elegant/*`
- 后端为支持表格浏览补了 `GET /face/entity/list`（分页）+ `GET /face/entity/detail`（含 faces），
  对应 facebody `ListFaceEntities` / `GetFaceEntity`；新增权限码 `face:entity:list`

## 约束与备注

- **图片来源**：facebody 的 `AddFace/SearchFace/DetectFace` 只收 `image_url`（必须 OSS 可访问），
  不收文件字节。接口接收 `UploadFile` → 写临时文件 → `viapi.fileutils.FileUtils.get_oss_url`
  上传阿里云托管 OSS 拿 URL → 再调 facebody（复用同一组 AccessKey，不走项目 STORAGE 模块）。
- **同步 SDK 异步化**：facebody SDK 与 FileUtils 均为同步阻塞，所有调用经 `asyncio.to_thread` 包装，
  Client/FileUtils 用 `lru_cache` 懒加载缓存。
- **实体命名**：直接用阿里云 `entity_id`，不引入本地映射表（去掉原脚本 `entity_mapper`）。
- **错误处理**：service 层失败抛 `core.exception.errors` 异常（未启用/缺密钥 → `ServerError`，
  阿里云/网关失败 → `GatewayError`），由端点统一成 `ResponseModel`；不再返回 `False`/`[]`。
- **db_name 缺省**：接口 `db_name` 为空时取 `settings.FACE.DEFAULT_DB_NAME`。
- **权限码**：`face:db:create/db:list/entity:add/entity:delete/image:add/image:delete/search/detect`
  （路由级 `current_user` + 每端点 `require_permission`；非超管需 sys_menu 种子，超管直通）。
- **版本**：实际安装 `alibabacloud-facebody20191230==5.1.2`；已核对响应字段名——
  `db_list[].name`、`AddFace.data.face_id`、`SearchFace.data.match_list[].face_items[].{entity_id,confidence}`、
  `DetectFace.data.{face_count,face_rectangles,face_probability_list}`。

### 与既有"机器人人脸"功能的区别

2026-06-11 的 `face-*` 记忆是**机器人配置**里的人像 photo（`robot_face_config` 表 + 上传预览），
属于 robot 模块；本模块是**阿里云人脸库**的库级增删查，二者独立，无表关联。

## 相关文件

- 新模块：`backend/modules/face/`（`router.py`、`endpoints/face.py`、
  `services/face_service.py`、`schemas/face.py`）
- 配置：`backend/core/config/settings_model.py`、`backend/core/config/settings.py`、
  `backend/.env.dev`
- 依赖：`backend/pyproject.toml`、`backend/uv.lock`
- 注册：`backend/main.py`
- 菜单/权限种子：`backend/database/alembic/versions/0036_seed_face_menu.py`
  （menu id 3000000000000090，button 091-098；挂在 manage 目录 2874692539129857 下，sort=12）
- 参考源：仓库根目录 `face_recognition.py`（保留未改）

## 记录日期

2026-06-29
