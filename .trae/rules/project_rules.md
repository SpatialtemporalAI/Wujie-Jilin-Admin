你是一名资深项目工程师，负责设计和实现一个基于 FastAPI 的云原生项目。该项目需要考虑高可用性、可扩展性和安全性。项目采用微服务架构，前端基于 Vue 3 + Vite 构建，后端基于 FastAPI 框架。


# SmileX-Fastapi-Cloud 项目开发规范

## 一、目录结构规范

### 1.1 项目根目录
- **后端代码**：存放在 `backend/` 目录
- **前端代码**：存放在 `frontend/` 目录

### 1.2 后端目录结构
```
backend/
├── app/                 # 应用业务模型
│   ├── models/         # 业务模型定义
│   │   ├── business/   # 业务模型
│   │   ├── common/     # 公共基础模型
│   │   └── sys/        # 系统模型
├── core/               # 核心基础设施
│   ├── config/         # 配置管理
│   ├── database/       # 数据库管理
│   ├── exception/      # 异常处理
│   ├── log/            # 日志系统
│   ├── models/         # 基础模型
│   ├── redis/          # Redis 缓存
│   ├── response/       # 统一响应
│   ├── security/       # 安全认证
│   └── utils/          # 工具函数
├── modules/            # 业务模块（按模块划分）
│   ├── admin/          # 后台管理模块
│   │   ├── deps/       # 依赖注入
│   │   ├── endpoints/  # API 端点
│   │   ├── models/     # 模块数据模型
│   │   ├── services/   # 业务服务层
│   │   └── router.py   # 路由注册
│   └── app/            # 应用模块
├── alembic/            # 数据库迁移文件
├── scripts/            # 工具脚本
├── main.py             # 应用入口
└── pyproject.toml      # 项目配置
```

**后端模块规范**：
- 每个模块必须包含 `__init__.py` 文件
- 模块内部按功能划分为：`deps/`（依赖）、`endpoints/`（路由）、`models/`（模型）、`services/`（服务）

### 1.3 前端目录结构
```
frontend/
├── packages/           # 工作区子包
│   ├── alova/          # Alova 请求库封装
│   ├── axios/          # Axios 请求库封装
│   ├── color/          # 颜色工具
│   ├── hooks/          # 自定义 Hooks
│   ├── materials/      # UI 组件库
│   ├── scripts/        # 脚本工具
│   ├── uno-preset/     # UnoCSS 预设
│   └── utils/          # 工具函数
├── src/
│   ├── assets/         # 静态资源
│   ├── components/     # 公共组件
│   ├── constants/      # 常量定义
│   ├── enum/           # 枚举定义
│   ├── hooks/          # Hooks
│   ├── layouts/        # 布局组件
│   ├── locales/        # 国际化文件
│   │   └── langs/      # 语言包（zh-cn.ts, en-us.ts）
│   ├── plugins/        # 插件
│   ├── router/         # 路由配置
│   ├── service/        # API 服务
│   ├── store/          # 状态管理
│   ├── styles/         # 样式文件
│   ├── theme/          # 主题配置
│   ├── typings/        # TypeScript 类型声明
│   │   └── app.d.ts    # 应用类型声明
│   ├── utils/          # 工具函数
│   └── views/          # 页面组件（按页面划分）
│       ├── home/       # 首页
│       └── manage/     # 管理页
```

**前端页面规范**：
- 每个页面必须有独立文件夹
- 文件夹下必须包含主 `.vue` 文件
- 相关子组件放在 `modules/` 子目录
- 共享逻辑放在 `shared.ts` 文件中

---

## 二、后端开发规范

### 2.1 环境与依赖管理
- **包管理工具**：使用 `uv` 作为项目管理工具
- **环境激活**：Windows 系统执行 `.\venv\Scripts\activate.bat`
- **依赖安装**：`uv install` 或 `uv pip install <package>`
- **Python 版本**：要求 3.11+

### 2.2 数据库规范
- **ORM 框架**：SQLAlchemy 2.0+
- **迁移工具**：Alembic
- **迁移命令**：
  - 创建迁移：`alembic revision --autogenerate -m "描述信息"`
  - 应用迁移：`alembic upgrade head`
  - 回退迁移：`alembic downgrade -1`
- **注意**：使用 `uv` 时需在命令前加 `uv run`

### 2.3 响应数据模型规范
- **所有响应数据模型**必须继承自 `BaseRespEntity`
- 确保时间字段的正确格式化
- 统一响应格式在 `core/response/` 中定义

### 2.4 代码注释规范
- 所有类必须添加**类级注释**，说明类的用途和职责
- 所有函数必须添加**函数级注释**，说明功能、参数、返回值
- 复杂业务逻辑必须添加详细的行内注释

### 2.5 异常处理规范
- 必须对可能出现异常的代码进行 try-except 捕获
- 使用 `core/exception/` 中定义的自定义异常类
- 异常必须记录日志，并返回友好的错误信息

### 2.6 性能优化规范
- 数据库查询避免 N+1 问题，合理使用 joinedload
- 频繁访问的数据使用 Redis 缓存
- 大文件上传下载采用流式处理
- 异步接口优先使用 async/await

---

## 三、前端开发规范

### 3.1 环境与依赖管理
- **包管理工具**：优先使用 `pnpm`，其次是 `npm`
- **Node 版本**：要求 >= 20.19.0
- **pnpm 版本**：要求 >= 10.5.0
- **依赖安装**：`pnpm install`

### 3.2 新增页面规范
新增页面时必须完成以下配置：

1. **创建页面文件**：在 `src/views/` 下创建对应文件夹和 `.vue` 文件
2. **配置国际化**：
   - 修改 `src/locales/langs/zh-cn.ts` 添加中文翻译
   - 修改 `src/locales/langs/en-us.ts` 添加英文翻译
3. **配置类型声明**：修改 `src/typings/app.d.ts` 添加页面路由类型
4. **生成路由**：执行 `pnpm gen-route` 自动生成路由

### 3.3 TypeScript 类型安全
- 前端全面使用 TypeScript
- 所有变量、函数参数、返回值必须有明确的类型声明
- 修改数据结构时必须同步更新对应的类型声明文件
- 定期执行 `pnpm typecheck` 确保类型安全

### 3.4 常用脚本命令
```bash
# 开发模式（测试环境）
pnpm dev

# 开发模式（生产环境）
pnpm dev:prod

# 构建生产版本
pnpm build

# 构建测试版本
pnpm build:test

# 类型检查
pnpm typecheck

# 代码检查与修复
pnpm lint

# 生成路由
pnpm gen-route

# Git 提交
pnpm commit:zh
```

### 3.5 代码注释规范
- 所有类必须添加**类级注释**
- 所有函数必须添加**函数级注释**
- 复杂业务逻辑必须添加详细注释
- 类型声明文件必须有清晰的注释说明

### 3.6 组件开发规范
- 公共组件放在 `src/components/` 目录
- 页面级组件放在对应页面的 `modules/` 目录
- 组件命名使用 PascalCase
- Props 必须使用 TypeScript 接口定义

---

## 四、Git 提交规范

### 4.1 提交流程
- 前端项目使用 `pnpm commit:zh` 进行交互式提交
- 提交信息必须清晰描述变更内容
- 提交前确保通过 `pnpm typecheck` 和 `pnpm lint`

### 4.2 代码审查
- 提交前必须通过所有类型检查和 lint 检查
- 重要功能变更需要 Code Review

---

## 五、测试与部署

### 5.1 后端启动
```bash
# 激活虚拟环境
.\venv\Scripts\activate.bat

# 启动开发服务器
uvicorn main:app --reload

# 或使用 Python 直接运行
python main.py
```

### 5.2 前端启动
```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 5.3 API 文档
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

---

## 六、其他注意事项

1. **操作系统**：本项目主要在 Windows 系统下开发
2. **配置文件**：环境配置文件位于 `backend/.env.*` 和 `frontend/.env.*`
3. **日志系统**：后端日志配置在 `backend/config/logging_*.ini`
4. **文档目录**：项目相关文档存放在 `.trae/documents/` 目录
