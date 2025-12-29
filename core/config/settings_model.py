#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目配置文件模型
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from typing import Optional, Tuple
class DatabaseModel(BaseModel):
    """数据库配置模型"""
    URL: str = Field(..., description="数据库连接地址")
    ECHO: bool = Field(False, description="是否打印数据库查询日志")
    POOL_SIZE: int = Field(10, description="数据库连接池大小")
    MAX_OVERFLOW: int = Field(20, description="数据库连接池溢出大小")
    POOL_TIMEOUT: int = Field(60, description="数据库连接池超时时间")
    POOL_RECYCLE: int = Field(300, description="数据库连接回收时间")
    POOL_PRE_PING: bool = Field(True, description="数据库连接预检查")
    POOL_USE_LIFO: bool = Field(
        True, description="数据库连接使用LIFO"
    )  # 优先使用最近创建的连接（提升性能）
class ServiceModel(BaseModel):
    """服务配置模型"""
    NAME: str = Field("SpatialtemporalAI Cloud", description="服务名称")
    VERSION: str = Field("1.0.0", description="服务版本")
    PREFIX: str = Field("/st", description="服务前缀")
class JWTModel(BaseModel):
    """JWT配置模型"""
    SECRET_KEY: str = Field("token", description="JWT密钥")
    ALGORITHM: str = Field("HS256", description="JWT算法")
    AUDIENCE: str = Field("app-user", description="JWT受众")
    SECRET_SALT: str = Field("SECRET_SALT", description="JWT密钥盐")
    ACCESS_LIFETIME: int = Field(3600, description="访问令牌有效期")
    REFRESH_LIFETIME: int = Field(86400, description="刷新令牌/会话有效期")
    SESSION_PREFIX: str = Field("JWT_SESSION:", description="会话前缀")
class LocalUploadModel(BaseModel):
    """本地上传配置模型"""
    BASE_DIR: str = Field("uploads", description="本地上传基础目录")
    MAX_FILE_SIZE: int = Field(10 * 1024 * 1024, description="最大文件大小(字节)")
    ALLOWED_EXTENSIONS: Optional[Tuple[str, ...]] = Field(
        None, description="允许的文件扩展名"
    )
class LogModel(BaseModel):
    """日志配置模型"""
    INI: str = Field("logging.ini", description="日志配置文件")
    DIR: str = Field("logs", description="日志目录")
class TraceIdModel(BaseModel):
    """TraceId 模型"""
    REQUEST_HEADER_KEY: str = "X-Request-ID"
    LOG_LENGTH: int = 32  # UUID 长度，必须小于等于 32
    LOG_DEFAULT_VALUE: str = "-"
class DatatimeModel(BaseModel):
    """时间配置模型"""
    TIMEZONE: str = Field("Asia/Shanghai", description="时区")
    FORMAT: str = Field("%Y-%m-%d %H:%M:%S", description="时间格式")
class RedisPoolModel(BaseModel):
    """Redis连接池模型"""
    HOST: str = Field("localhost", description="Redis主机")
    PORT: int = Field(6379, description="Redis端口")
    DB: int = Field(0, description="Redis数据库")
    PASSWORD: str = Field("", description="Redis密码")
    DECODE_RESPONSES: bool = Field(True, description="是否自动解码为字符串")
    MAX_CONNECTIONS: int = Field(20, description="最大连接数")
    SOCKET_TIMEOUT: int = Field(5, description="Socket超时时间(秒)")
    SOCKET_CONNECT_TIMEOUT: int = Field(3, description="连接超时时间(秒)")
    SOCKET_KEEPALIVE: bool = Field(True, description="是否保持连接")
    SOCKET_KEEPALIVE_OPTIONS: dict = Field(None, description="保持连接选项")
    RETRY_ON_TIMEOUT: bool = Field(False, description="超时是否重试")