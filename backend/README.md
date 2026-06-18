# Wujie-Jilin-Admin_Cloud

一个基于 FastAPI 构建的现代化云服务平台后端系统，提供完整的用户认证、权限管理、数据处理和API服务能力。

## 🌟 功能特点

### 核心功能
- **用户认证系统**：基于 JWT 的安全认证机制，支持多端认证
- **权限管理**：细粒度的角色权限控制（RBAC）
- **数据管理**：完整的数据库操作支持，包含连接池管理
- **缓存系统**：Redis 集成，支持高效缓存策略
- **模块化设计**：清晰的模块划分，便于扩展和维护
- **环境配置**：支持多环境（开发、测试、生产）配置管理

### 技术特性
- **异步处理**：基于 Python 异步特性，提供高性能服务
- **类型安全**：全面使用 Pydantic 进行数据验证和类型检查
- **ORM 支持**：SQLAlchemy 2.0 集成，支持复杂数据库操作
- **数据库迁移**：Alembic 支持，方便数据库结构变更管理
- **日志系统**：完善的日志记录，支持不同环境的日志配置
- **CORS 支持**：跨域资源共享配置，便于前端集成

## 🛠️ 技术栈

| 技术/框架 | 版本 | 用途 |
|---------|------|------|
| Python | 3.11+ | 开发语言 |
| FastAPI | 0.127+ | Web 框架 |
| SQLAlchemy | 2.0.45+ | ORM 框架 |
| Alembic | 1.17.2+ | 数据库迁移 |
| asyncpg | 0.31.0+ | PostgreSQL 异步驱动 |
| Redis | 7.1.0+ | 缓存系统 |
| PyJWT | 2.10.1+ | JWT 认证 |
| Pydantic | 2.x | 数据验证 |
| Uvicorn | 0.40.0+ | ASGI 服务器 |
| Gunicorn | 23.0.0+ | 生产环境服务器 |
| mcp | 1.0+ | MCP SDK（FastMCP） |
| httpx | 0.27+ | 异步 HTTP 客户端 |

## 🚀 快速开始

### 环境要求
- Python 3.11 或更高版本
- PostgreSQL 14 或更高版本
- Redis 6.2 或更高版本

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Wujie-jilin-admin
```

2. **安装依赖**
```bash
# 使用 uv 包管理器（推荐）
uv install

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境配置文件
cp .env.dev .env

# 根据实际情况修改 .env 文件中的配置（数据库连接、Redis 连接等）
```

4. **数据库初始化**
```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

5. **创建超级管理员**
```bash
python scripts/create_superuser.py
```

6. **启动开发服务器**
```bash
# 使用 uvicorn 直接运行
uvicorn main:app --reload

# 或使用 Python 运行
python main.py
```

7. **访问 API 文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 目录结构

```
├── app/                  # 应用相关模型
│   ├── models/           # 业务模型定义
│   └── asr/              # ASR 相关功能
├── core/                 # 核心功能模块
│   ├── config/           # 配置管理
│   ├── database/         # 数据库连接与管理
│   ├── exception/        # 异常处理
│   ├── log/              # 日志系统
│   ├── models/           # 基础模型定义
│   ├── redis/            # Redis 连接与管理
│   ├── response/         # 统一响应格式
│   ├── security/         # 安全相关功能
│   └── utils/            # 工具函数
├── mcp/                  # MCP 工具模块
│   ├── registry.py       # 工具注册表与 @register_tool 装饰器
│   ├── server.py         # FastMCP 服务器创建与 ASGI 挂载
│   ├── template.py       # 工具代码模板生成器
│   ├── standalone.py     # 独立进程管理（启动/停止/状态）
│   ├── context.py        # MCP 鉴权上下文
│   ├── http_client.py    # 上游 HTTP 客户端
│   ├── result.py         # 结果辅助函数
│   └── tools/            # 自动发现的工具目录
├── modules/              # 业务模块
│   ├── admin/            # 后台管理模块
│   │   ├── deps/         # 依赖注入
│   │   ├── endpoints/    # API 端点
│   │   ├── models/       # 模块模型
│   │   └── router.py     # 路由定义
│   └── app/              # 应用模块
│       ├── deps/         # 依赖注入
│       ├── endpoints/    # API 端点
│       ├── models/       # 模块模型
│       └── router.py     # 路由定义
├── scripts/              # 工具脚本
├── alembic/              # 数据库迁移文件
├── .env.*                # 环境配置文件
├── alembic.ini           # Alembic 配置
├── logging.ini           # 日志配置
├── main.py               # 应用入口
├── pyproject.toml        # 项目配置
└── README.md             # 项目文档
```

## 🎯 核心功能

### 1. 用户认证系统
- JWT 令牌生成与验证
- 用户名/密码登录
- 令牌刷新机制
- 多端登录支持

### 2. 权限管理
- 角色定义与分配
- 权限控制与验证
- 细粒度的 API 访问控制

### 3. 数据管理
- 数据库连接池管理
- 异步数据库操作
- 事务支持
- 数据迁移与版本控制

### 4. 缓存系统
- Redis 连接池管理
- 高效缓存操作
- 缓存失效策略

### 5. 日志系统
- 多环境日志配置
- 结构化日志格式
- 日志级别控制
- 日志文件轮转

### 6. MCP 工具平台
- 基于 Python `mcp` SDK (FastMCP) 的 MCP 服务器
- Streamable HTTP 传输，挂载在 `/mcp` 路径下
- `@register_tool` 装饰器 + `pkgutil` 自动发现工具
- 管理后台支持在线创建工具（自动生成代码）、测试调用
- 支持独立进程部署（通过管理 API 启动/停止）

MCP 环境变量配置（在 `.env` 中设置，使用 `MCP__` 前缀）：

```bash
MCP__ENABLED=true                # 是否启用 MCP
MCP__NAME=Wujie-Jilin-Admin MCP Server      # 服务器名称
MCP__HOST=127.0.0.1              # 独立服务地址
MCP__PORT=9000                   # 独立服务端口
MCP__UPSTREAM_BASE_URL=http://127.0.0.1:8000  # 上游应用 URL
```

管理 API 端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/sys/mcp/add` | 创建 MCP 工具 |
| POST | `/admin/sys/mcp/list` | 获取已注册工具列表 |
| POST | `/admin/sys/mcp/test` | 测试工具调用 |
| POST | `/admin/sys/mcp/routes` | 获取 MCP 路由信息 |
| POST | `/admin/sys/mcp/status` | 获取 MCP 服务器状态 |
| POST | `/admin/sys/mcp/start` | 启动独立 MCP 服务 |
| POST | `/admin/sys/mcp/stop` | 停止独立 MCP 服务 |

## 📚 API 文档

项目集成了自动生成的 API 文档，提供两种查看方式：

- **Swagger UI**: 提供交互式的 API 文档，支持在线测试 API
  - 访问地址: http://localhost:8000/docs

- **ReDoc**: 提供更简洁的 API 文档展示
  - 访问地址: http://localhost:8000/redoc

## 🚀 部署说明

### 开发环境
```bash
# 使用 uvicorn 运行
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

1. **使用项目内置脚本（推荐）**

`backend/start_prod.sh` 已封装好 gunicorn + uvicorn worker 启动逻辑，自动 `export ENVIR=prod` 加载 `.env.prod`：
```bash
cd backend && ./start_prod.sh
# 自定义参数（可选）
HOST=0.0.0.0 PORT=8000 WORKERS=4 ./start_prod.sh
```
默认参数 `-w 4 --timeout 120 --max-requests 5000 --max-requests-jitter 500`，与 `deploy/smilex-cloud.service` 对齐；支持 `HOST/PORT/WORKERS/TIMEOUT/MAX_REQUESTS/MAX_REQUESTS_JITTER/LOG_LEVEL` 环境变量覆盖。

> 仅支持 Linux/WSL（gunicorn 不支持 Windows）。正式生产长期运行推荐 systemd，参考 `deploy/smilex-cloud.service` + `deploy/deploy.sh`。

2. **直接使用 Gunicorn + Uvicorn（手动拼参数）**
```bash
ENVIR=prod gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

3. **Docker 部署**
```dockerfile
# 示例 Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIR=prod
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## 🔧 开发指南

### 数据库迁移
> 如果使用 `uv` 需在前面加上 `uv run`
```bash
# 创建新的迁移文件
alembic revision --autogenerate -m "描述信息"

# 应用所有迁移
alembic upgrade head

# 回退到上一个版本
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 代码规范

项目使用标准的 Python 代码规范，建议使用以下工具进行代码检查：

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

## 📈 接下来的发展方向

基于现有功能，以下是推荐的发展方向：

### 1. 完善 API 端点
- 扩展用户管理功能（创建、更新、删除用户）
- 实现角色权限管理的完整 API
- 添加更多业务模块的 API 端点
- 实现数据统计和报表功能

### 2. 增强数据验证和错误处理
- 完善输入数据验证
- 提供更详细的错误信息
- 实现自定义异常类
- 添加请求参数验证中间件

### 3. 增加测试用例
- 单元测试：测试核心功能模块
- 集成测试：测试模块间的交互
- API 测试：测试 API 端点的功能和性能
- 负载测试：测试系统在高负载下的表现

### 4. 完善文档
- 补充 API 接口文档
- 编写模块功能说明文档
- 增加开发和部署指南
- 提供示例代码和使用教程

### 5. 增强监控和日志
- 添加性能监控指标
- 实现分布式追踪
- 增加日志分析工具集成
- 实现异常报警机制

### 6. 性能优化
- 数据库查询优化
- 实现更高效的缓存策略
- 优化 API 响应时间
- 实现异步任务处理

### 7. 扩展业务功能
- 根据项目需求添加新的业务模块
- 实现数据导入导出功能
- 增加文件上传下载功能
- 集成第三方服务

### 8. 完善部署流程
- 实现 CI/CD 流水线
- 容器化部署（Docker、Kubernetes）
- 自动化测试和部署
- 实现灰度发布机制

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目！

### 提交 Pull Request 前请确保：
1. 代码符合项目的代码规范
2. 所有测试用例通过
3. 添加了适当的文档
4. 提交信息清晰明了

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

## 📧 联系方式

如有任何问题或建议，欢迎通过以下方式联系我们：

- GitHub Issues：[https://github.com/SpatialtemporalAI/Wujie-jilin-admin]

---

感谢您使用 Wujie-Jilin-Admin_Cloud！ 🎉