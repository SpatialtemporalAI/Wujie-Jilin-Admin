# AGENT.MD

## 目的

本文件是本仓库内 AI 协作规则的唯一真源。

`.codex/`、`.claude/`、`.cursor/`、`.trae/` 下的规则文件仅作为兼容适配层，不能再次演变成各自独立维护的 project rule 副本。

## 读取顺序

按下面顺序加载项目上下文：

1. `AGENT.MD`
2. `aiDoc/README.md`
3. 按任务读取以下目录中的相关文件：
   - `aiDoc/relations/`
   - `aiDoc/modules/`
   - `aiDoc/frontend-backend/`
   - `aiDoc/examples/`
   - `aiDoc/memory/`
4. 仅在当前工具确实依赖时，再读取工具目录下的适配文件

若内容冲突，以 `AGENT.MD` 为准。

## 仓库概览

- `backend/`: Python 3.11+ FastAPI + SQLAlchemy 2.0 后端
- `frontend/`: Vue 3 + Vite + NaiveUI 前端
- `aiDoc/`: AI 协作文档层
- `.trae/`、`.claude/`、`.cursor/`: 工具兼容适配层

## 工程规则

### 架构

- 保持现有后端分层：`Endpoint -> Service -> Model`
- Endpoint 层处理 HTTP 相关逻辑，Service 层不要依赖 FastAPI 请求对象
- 对外接口的 Swagger 注释必须和真实行为保持一致
- 优先沿用项目现有模式，不做无关的大改

### 前后端协作

- 明确请求与响应契约
- 保持统一响应结构：`{ code, msg, data, request_id, err_code }`
- 保持统一分页结构：`{ records, page, page_size, total, total_pages }`
- 前后端字段名和数据类型保持一致
- Status 字段桥接：后端 `bool` → 前端 `"1"` / `"2"` 字符串
- 涉及跨栈边界变更时，同步更新 `aiDoc/frontend-backend/`

### 模块与目录

- 后端模块放在 `backend/modules/<name>/`，含 `endpoints/`、`services/`、`schemas/`、`deps/`
- 前端页面放在 `frontend/src/views/<name>/`
- 稳定的模块职责、入口和边界说明放到 `aiDoc/modules/`

### 示例文档

- `aiDoc/examples/` 是讲解型示例层
- 示例文档不是要求逐字复制，而是告诉 AI 该如何按项目标准组织代码
- 当 AI 需要新增某一层文件时，应先阅读对应示例，再开始实现

### 记忆规则

- `aiDoc/memory/long-term/` 用于记录长期稳定的用户偏好、协作方式和跨任务约束
- `aiDoc/memory/business/` 用于记录每次用户提出的业务需求
- 这里的"业务需求"指新增或修改模块、接口、页面、流程、业务规则等项目需求
- 当用户提出业务需求时，AI 必须新增或更新一条 `business` 记忆，并同步更新需求索引
- 当某条业务需求沉淀成长期稳定偏好时，再提炼到 `long-term`

### 文档维护

- `AGENT.MD` 只保留高层、稳定、跨任务的规则
- 细节上下文写入 `aiDoc/`
- 结构关系放在 `aiDoc/relations/`
- 示例写法放在 `aiDoc/examples/`
- 长期记忆与业务记忆放在 `aiDoc/memory/`
- 若项目级 AI 规则发生变化，先改 `AGENT.MD`，再按需更新适配层

### 代码读取约束

- 无论什么情况，都不要直接读取 `node_modules/`、`.venv/`、`__pycache__/` 中的代码
- 如需了解第三方库行为，优先查看项目源码中的调用方式、锁文件、配置文件、官方文档或包的公开类型/说明文件

## AI 文档索引

- `aiDoc/README.md`
- `aiDoc/relations/repo-profile.md`
- `aiDoc/relations/development-workflow.md`
- `aiDoc/relations/system-map.md`
- `aiDoc/modules/backend-layer-rules.md`
- `aiDoc/modules/module-development.md`
- `aiDoc/modules/mcp-guide.md`
- `aiDoc/modules/plugin-development.md`
- `aiDoc/frontend-backend/boundary.md`
- `aiDoc/frontend-backend/frontend-rules.md`
- `aiDoc/frontend-backend/frontend-utils.md`
- `aiDoc/examples/README.md`
- `aiDoc/examples/backend/`
- `aiDoc/examples/frontend/`
- `aiDoc/memory/README.md`
- `aiDoc/memory/project-memory.md`
- `aiDoc/memory/long-term/`
- `aiDoc/memory/business/`

