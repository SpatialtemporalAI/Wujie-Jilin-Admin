#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目配置文件模型
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from typing import Optional, Tuple
from database import DatabaseModel
from typing import List


class ServiceModel(BaseModel):
    """服务配置模型"""

    NAME: str = Field("Wujie-Jilin-Admin Cloud", description="服务名称")
    VERSION: str = Field("1.0.0", description="服务版本")
    PREFIX: str = Field("/st", description="服务前缀")
    OPENAPI_ENABLE_IN_PROD: bool = Field(
        False, description="生产环境是否启用OpenAPI文档"
    )
    BASE_URL: str = Field(
        "",
        description="对外可访问的基础 URL（含协议+host+port），用于拼接文件可访问 URL；为空则只返回相对路径",
    )
    INTERNAL_TOKEN: str = Field(
        "",
        description="服务间内部共享密钥；非空时启用签名 URL 模式（HMAC），同时允许通过 X-Internal-Token header 免 JWT 访问 preview 端点",
    )
    FILE_PREVIEW_TTL_SECONDS: int = Field(
        600, description="签名 URL 默认有效期（秒）；过期后导览服务需重新触发推送"
    )


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
    ALLOWED_EXTENSIONS: Optional[List[str]] = Field(
        None, description="允许的文件扩展名"
    )


class StorageModel(BaseModel):
    """存储平台配置模型"""

    PLATFORM: str = Field("local", description="存储平台：local, oss")


class LogModel(BaseModel):
    """日志配置模型"""

    INI: str = Field("logging.ini", description="日志配置文件")
    DIR: str = Field("logs", description="日志目录")


class TraceIdModel(BaseModel):
    """TraceId 模型"""

    REQUEST_HEADER_KEY: str = "X-Request-ID"
    LOG_LENGTH: int = 32  # UUID 长度，必须小于等于 32
    LOG_DEFAULT_VALUE: str = "-"


class SecurityModel(BaseModel):
    """安全配置模型"""

    # cors配置
    ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的Origin白名单",
    )
    ALLOWED_HOSTS: Tuple[str, ...] = Field(
        ("localhost", "127.0.0.1"),
        description="允许的Host白名单",
    )
    TRUSTED_PROXIES: Tuple[str, ...] = Field(
        ("127.0.0.1", "::1"),
        description="可信反向代理IP列表",
    )
    MAX_REQUEST_SIZE: int = Field(2 * 1024 * 1024, description="最大请求体大小(字节)")
    HSTS_ENABLED: bool = Field(False, description="是否启用 HSTS")
    HSTS_VALUE: str = Field(
        "max-age=31536000; includeSubDomains",
        description="HSTS 响应头内容",
    )
    CSP_POLICY: str = Field(
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        description="Content-Security-Policy 策略",
    )
    REFERRER_POLICY: str = Field(
        "strict-origin-when-cross-origin",
        description="Referrer-Policy",
    )
    PERMISSIONS_POLICY: str = Field(
        "camera=(), microphone=(), geolocation=()",
        description="Permissions-Policy",
    )


class DatatimeModel(BaseModel):
    """时间配置模型"""

    TIMEZONE: str = Field("Asia/Shanghai", description="时区")
    FORMAT: str = Field("%Y-%m-%d %H:%M:%S", description="时间格式")


class MCPModel(BaseModel):
    """MCP 配置模型"""

    ENABLED: bool = Field(True, description="是否启用 MCP 模块")
    NAME: str = Field("Wujie-Jilin-Admin MCP Server", description="MCP 服务器名称")
    VERSION: str = Field("1.0.0", description="MCP 版本")
    HOST: str = Field("127.0.0.1", description="独立服务地址")
    PORT: int = Field(9000, description="独立服务端口")
    BASE_URL: str = Field("", description="MCP 服务基础 URL")
    UPSTREAM_BASE_URL: str = Field("http://127.0.0.1:8000", description="上游应用 URL")
    AUTH_HEADER: str = Field("Authorization", description="鉴权 Header 名称")
    REQUEST_TIMEOUT: int = Field(30, description="请求超时时间(秒)")
    PROCESS_META_FILE: str = Field("mcp_process.json", description="进程元数据文件")


class RateLimitPathRuleModel(BaseModel):
    """按接口路径细粒度限流规则"""

    PATH: str = Field(..., description="路径前缀匹配（startswith）")
    METHOD: str = Field("*", description="HTTP 方法，* 表示全部")
    PER_MINUTE: int = Field(..., description="每分钟允许次数（按 IP 聚合）")


class RateLimitModel(BaseModel):
    """限流与黑名单配置"""

    ENABLED: bool = Field(True, description="是否启用限流中间件")
    IP_PER_MINUTE: int = Field(120, description="单 IP 每分钟最大请求数")
    USER_PER_MINUTE: int = Field(300, description="单用户每分钟最大请求数")
    LOGIN_FAIL_MAX: int = Field(5, description="登录失败次数上限")
    LOGIN_FAIL_WINDOW: int = Field(600, description="登录失败统计窗口(秒)")
    LOGIN_FAIL_BLOCK_TTL: int = Field(1800, description="登录失败拉黑时长(秒)")
    CAPTCHA_TRIGGER_THRESHOLD: int = Field(2, description="触发滑块验证的登录失败次数")
    CAPTCHA_TOLERANCE: int = Field(5, description="滑块验证位置容差(像素)")
    CAPTCHA_TOKEN_TTL: int = Field(300, description="验证码令牌有效期(秒)")
    CAPTCHA_MAX_VERIFY_ATTEMPTS: int = Field(5, description="单次验证码最大验证次数")
    BLACKLIST_REDIS_TTL: int = Field(
        86400, description="Redis 黑名单兜底 TTL(秒)，到期重新从 DB 同步"
    )
    WHITELIST_PATH_PREFIXES: Tuple[str, ...] = Field(
        (
            "/docs",
            "/redoc",
            "/openapi.json",
        ),
        description="不参与限流的路径前缀白名单",
    )
    WHITELIST_IPS: Tuple[str, ...] = Field(
        ("127.0.0.1", "::1"),
        description="不参与限流和黑名单检查的 IP 白名单",
    )
    PATH_RULES: List[RateLimitPathRuleModel] = Field(
        default_factory=list,
        description="按路径细粒度限流规则（按 IP 聚合）",
    )


class PluginModel(BaseModel):
    """插件配置模型"""

    ENABLED: List[str] = Field(
        default_factory=list,
        description="启用的插件列表，如 ['multi_tenant']",
    )


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


class GrpcModel(BaseModel):
    """gRPC 客户端配置"""

    ENABLED: bool = Field(
        False, description="是否启用 gRPC（关闭时所有推送/拉取静默跳过）"
    )
    MAP_SERVICE_ADDR: str = Field(
        "127.0.0.1:50051", description="MapService 地址 host:port"
    )
    CONFIG_SERVICE_ADDR: str = Field(
        "127.0.0.1:50052",
        description="ConfigService 地址 host:port（voice/speed/battery/face 共用）",
    )
    TIMEOUT_SECONDS: float = Field(30.0, description="单次 RPC 超时(秒)")


class MerchantModel(BaseModel):
    """商户开放 API 配置模型"""

    ENCRYPT_KEY: str = Field(
        "wujie-merchant-default-key-please-change",
        description="api_secret 可逆加密密钥（passphrase，生产环境必须修改）",
    )
    SIGN_TTL_SECONDS: int = Field(
        300, description="HMAC 签名时间戳容差窗口(秒)"
    )
    NONCE_TTL_SECONDS: int = Field(
        300, description="nonce 防重放缓存时长(秒)"
    )
    API_KEY_PREFIX: str = Field("mk_", description="api_key 前缀")
    API_SECRET_PREFIX: str = Field("sk_", description="api_secret 前缀")


class FaceRecognitionModel(BaseModel):
    """阿里云人脸识别（Facebody）配置模型"""

    ENABLED: bool = Field(False, description="是否启用阿里云人脸识别")
    ACCESS_KEY_ID: str = Field("", description="阿里云 AccessKey ID")
    ACCESS_KEY_SECRET: str = Field("", description="阿里云 AccessKey Secret")
    ENDPOINT: str = Field(
        "facebody.cn-shanghai.aliyuncs.com", description="人脸识别服务端点"
    )
    REGION_ID: str = Field("cn-shanghai", description="阿里云区域 ID")
    DEFAULT_DB_NAME: str = Field("default", description="默认人脸库名称")


class LiveKitModel(BaseModel):
    """LiveKit 实时音视频配置模型"""

    ENABLED: bool = Field(False, description="是否启用 LiveKit 视频流")
    API_KEY: str = Field("", description="LiveKit API Key")
    API_SECRET: str = Field("", description="LiveKit API Secret")
    WS_URL: str = Field("", description="LiveKit WebSocket URL（wss://...）")
    TOKEN_TTL_SECONDS: int = Field(
        3600, description="观众 Token 有效期（秒）"
    )
    VIEWER_HEARTBEAT_TTL_SECONDS: int = Field(
        60, description="观众心跳租约 TTL（秒）"
    )
    VIEWER_HEARTBEAT_INTERVAL_SECONDS: int = Field(
        15, description="观众心跳间隔（秒）"
    )
    VIEWERS_SET_TTL_SECONDS: int = Field(
        7200, description="观众集合兜底过期时间（秒）"
    )
