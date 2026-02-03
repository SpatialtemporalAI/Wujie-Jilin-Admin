# 模块开发规则

## 1. 目录结构

### 标准MVC结构
```
modules/
  ├── {module_name}/
  │   ├── endpoints/       # 控制器层，处理HTTP请求
  │   │   ├── __init__.py
  │   │   └── {module}.py   # 按功能模块拆分
  │   ├── services/        # 服务层，处理业务逻辑
  │   │   ├── __init__.py
  │   │   └── {module}/     # 按功能模块拆分
  │   ├── models/          # 数据模型层
  │   │   ├── __init__.py
  │   │   └── {module}.py
  │   ├── deps/            # 依赖注入
  │   ├── router.py        # 路由配置
  │   └── main.py          # 模块入口
```

## 2. 分层职责

### 2.1 Endpoints (控制器层)
- **职责**：处理HTTP请求和响应
- **特点**：
  - 只负责请求参数验证和响应格式化
  - 调用Service层处理业务逻辑
  - 不直接操作数据库
  - 处理HTTP相关的异常

### 2.2 Services (服务层)
- **职责**：处理核心业务逻辑
- **特点**：
  - 包含所有业务逻辑
  - 直接操作数据库
  - 处理业务规则和异常
  - 提供可复用的业务功能

### 2.3 Models (模型层)
- **职责**：定义数据结构和数据库映射
- **特点**：
  - 使用SQLAlchemy ORM定义
  - 包含数据字段和关系定义
  - 不包含业务逻辑

## 3. 代码规范

### 3.1 命名规范
- **文件命名**：小写蛇形命名法，如 `user_service.py`
- **类命名**：大驼峰命名法，如 `UserService`
- **函数命名**：小写蛇形命名法，如 `get_user_list`
- **变量命名**：小写蛇形命名法，如 `user_id`

### 3.2 注释规范
- **文件头部**：添加文件描述
- **类注释**：添加类的功能描述
- **函数注释**：添加函数的功能、参数和返回值描述
- **复杂逻辑**：添加详细的逻辑说明

### 3.3 异常处理
- **Endpoints**：捕获Service层抛出的异常并转换为HTTP响应
- **Services**：抛出业务异常，不处理HTTP相关异常
- **使用统一**：使用core.exception.errors中定义的异常类

## 4. 开发流程

1. **定义模型**：在models目录下定义数据模型
2. **实现服务**：在services目录下实现业务逻辑
3. **创建接口**：在endpoints目录下创建HTTP接口
4. **配置路由**：在router.py中配置路由
5. **测试验证**：确保接口正常工作

## 5. 示例

### 5.1 模型定义
```python
# models/user.py
from core.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Boolean

class User(Base):
    """
    用户模型
    """
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
```

### 5.2 服务实现
```python
# services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.user import User
from core.exception.errors import NotFoundError

class UserService:
    """
    用户服务类
    """
    @staticmethod
    async def get_user_list(db: AsyncSession) -> List[User]:
        """
        获取用户列表
        """
        result = await db.execute(select(User))
        return result.scalars().all()
```

### 5.3 接口实现
```python
# endpoints/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse
from app.models.user import User
from modules.admin.services.user_service import UserService

user_router = APIRouter(
    prefix="/user",
    tags=["用户管理"]
)

@user_router.get("/list", response_model=BaseResponse[List[User]])
async def get_user_list(
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取用户列表
    """
    users = await UserService.get_user_list(db)
    return BaseResponse(data=users)
```

## 6. 注意事项

1. **避免业务逻辑重复**：将通用业务逻辑放在Service层
2. **保持Endpoints简洁**：只处理HTTP相关操作
3. **使用异步操作**：所有数据库操作使用异步方法
4. **统一异常处理**：使用标准异常类
5. **添加适当注释**：提高代码可读性
6. **遵循命名规范**：保持代码风格一致

## 7. 技术栈

- **Web框架**：FastAPI
- **ORM**：SQLAlchemy 2.0
- **数据库**：PostgreSQL
- **异步**：asyncio
- **依赖注入**：FastAPI Depends
- **类型提示**：Python 3.9+

## 8. 版本控制

- 遵循语义化版本规范
- 每次修改后更新版本号
- 编写详细的变更日志

## 9. 测试要求

- 为每个Service层方法编写单元测试
- 为每个Endpoint编写集成测试
- 确保测试覆盖率达到80%以上

## 10. 部署规范

- 使用Docker容器化部署
- 配置环境变量管理
- 实现CI/CD自动化流程

---

本规则适用于所有模块开发，确保代码质量和可维护性。
