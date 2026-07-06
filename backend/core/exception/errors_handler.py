#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
import types
from typing import Any, Callable, Dict, Optional, Type, Union, get_args, get_origin
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.exceptions import RequestValidationError, ValidationException
from pydantic import BaseModel, ValidationError
from core.exception.errors import (
    BaseExceptionMixin,
    CustomError,
    ForbiddenError,
    GatewayError,
    NotFoundError,
    RequestError,
    ServerError,
    TokenError,
    AuthorizationError,
    ConflictError,
    HTTPError,
)
from core.response.response_schema import response_base, ResponseModel
from core.response.response_code import (
    CustomErrorCode,
    CustomResponseCode,
    StandardResponseCode,
)
from logging import getLogger
from core.utils.track_id import get_request_trace_id

logger = getLogger(__name__)


def setup_exception_global_handlers(app: FastAPI) -> None:
    # 注册404路由未找到处理器
    @app.exception_handler(404)
    async def not_found_route_handler(
        request: Request, exc: Exception
    ) -> ORJSONResponse:
        """\处理路由未找到的情况"""
        return await not_found_error_handler(
            request, NotFoundError(msg="请求的路由不存在")
        )

    # 自定义Pydantic验证异常处理器
    @app.exception_handler(RequestValidationError)
    async def global_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        return await validation_exception_handler(request, exc)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """
        全局捕获ValueError异常，并返回标准化的JSON响应
        """
        request_id = get_request_trace_id(request)
        # 构建响应
        response = ResponseModel(
            code=StandardResponseCode.HTTP_400,
            msg=str(exc),
            request_id=request_id,
        )
        # 记录日志
        logger.error(
            f"请求异常: path={request.url.path}, method={request.method}, "
            f"msg={response.msg}"
        )
        return ORJSONResponse(
            status_code=StandardResponseCode.HTTP_400, content=response.model_dump()
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    设置全局异常处理器
    Args:
        app: FastAPI 应用实例
    """
    # 注册自定义异常处理器
    app.exception_handler(BaseExceptionMixin)(base_exception_handler)
    app.exception_handler(RequestError)(request_error_handler)
    app.exception_handler(ForbiddenError)(forbidden_error_handler)
    app.exception_handler(NotFoundError)(not_found_error_handler)
    app.exception_handler(ServerError)(server_error_handler)
    app.exception_handler(GatewayError)(gateway_error_handler)
    app.exception_handler(TokenError)(token_error_handler)
    app.exception_handler(AuthorizationError)(authorization_error_handler)
    app.exception_handler(ConflictError)(conflict_error_handler)
    app.exception_handler(CustomError)(custom_error_handler)
    # 注册FastAPI内置异常处理器
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(ValidationError)(pydantic_validation_error_handler)
    # 注册通用异常处理器（捕获所有未处理的异常）
    app.exception_handler(Exception)(generic_exception_handler)


async def base_exception_handler(
    request: Request, exc: BaseExceptionMixin
) -> ORJSONResponse:
    """
    基础异常处理器
    Args:
        request: FastAPI 请求对象
        exc: 基础异常实例
    Returns:
        统一格式的JSON响应
    """
    request_id = get_request_trace_id(request)
    # 记录日志
    logger.error(
        f"请求异常: path={request.url.path}, method={request.method}, "
        f"code={exc.code}, msg={exc.msg}, request_id={request_id}"
    )
    # 构建响应
    response = ResponseModel(
        code=exc.code,
        err_code=exc.err_code.code if hasattr(exc, "err_code") else None,
        msg=exc.msg or "请求异常",
        data=exc.data,
        request_id=request_id,
    )
    return ORJSONResponse(status_code=exc.code, content=response.model_dump())


async def request_error_handler(request: Request, exc: RequestError) -> ORJSONResponse:
    """
    请求异常处理器
    """
    return await base_exception_handler(request, exc)


async def forbidden_error_handler(
    request: Request, exc: ForbiddenError
) -> ORJSONResponse:
    """
    禁止访问异常处理器
    """
    return await base_exception_handler(request, exc)


async def not_found_error_handler(
    request: Request, exc: NotFoundError
) -> ORJSONResponse:
    """
    资源不存在异常处理器
    """
    return await base_exception_handler(request, exc)


async def server_error_handler(request: Request, exc: ServerError) -> ORJSONResponse:
    """
    服务器异常处理器
    """
    request_id = get_request_trace_id(request)
    # 记录详细错误日志（包括堆栈信息）
    logger.error(
        f"服务器内部错误: path={request.url.path}, method={request.method}, "
        f"msg={exc.msg}, request_id={request_id}\n{traceback.format_exc()}"
    )
    err_code = None
    msg = exc.msg or "服务器内部错误"
    if hasattr(exc, "err_code"):
        err_code = exc.err_code.code
        msg = exc.err_code.msg or msg
    # 构建响应
    response = ResponseModel(
        code=StandardResponseCode.HTTP_500,
        err_code=exc.err_code.code if hasattr(exc, "err_code") else None,
        msg=msg,
        data=exc.data,
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=StandardResponseCode.HTTP_500, content=response.model_dump()
    )


async def gateway_error_handler(request: Request, exc: GatewayError) -> ORJSONResponse:
    """
    网关异常处理器
    """
    return await base_exception_handler(request, exc)


async def token_error_handler(request: Request, exc: TokenError) -> ORJSONResponse:
    """
    Token异常处理器
    """
    request_id = get_request_trace_id(request)
    # 记录日志
    logger.warning(
        f"Token验证失败: path={request.url.path}, method={request.method}, "
        f"msg={exc.detail}, request_id={request_id}"
    )
    # 构建响应
    response = ResponseModel(
        code=StandardResponseCode.HTTP_401,
        msg=exc.detail or "未授权",
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=StandardResponseCode.HTTP_401,
        content=response.model_dump(),
        headers=exc.headers,
    )


async def authorization_error_handler(
    request: Request, exc: AuthorizationError
) -> ORJSONResponse:
    """
    授权异常处理器
    """
    return await base_exception_handler(request, exc)


async def conflict_error_handler(
    request: Request, exc: ConflictError
) -> ORJSONResponse:
    """
    资源冲突异常处理器
    """
    return await base_exception_handler(request, exc)


async def custom_error_handler(request: Request, exc: CustomError) -> ORJSONResponse:
    """
    自定义异常处理器
    """
    request_id = get_request_trace_id(request)
    # 记录日志
    logger.error(
        f"自定义异常: path={request.url.path}, method={request.method}, "
        f"code={exc.code}, msg={exc.msg}, request_id={request_id}"
    )
    # 确保data不为None，以避免响应验证错误
    data = exc.data if exc.data is not None else {}
    # 构建响应
    response = ResponseModel(
        code=CustomResponseCode.HTTP_500.code,
        err_code=exc.code,
        msg=exc.msg or "服务器发生异常",
        data=data,
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=CustomResponseCode.HTTP_500.code, content=response.model_dump()
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> ORJSONResponse:
    """
    FastAPI HTTP异常处理器
    """
    request_id = get_request_trace_id(request)
    # 记录日志
    logger.error(
        f"HTTP异常: path={request.url.path}, method={request.method}, "
        f"status_code={exc.status_code}, detail={exc.detail}, request_id={request_id}"
    )
    # 构建响应
    response = ResponseModel(
        code=exc.status_code,
        err_code=exc.status_code,
        msg=str(exc.detail) if exc.detail else "HTTP异常",
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
        headers=exc.headers if exc.headers else {},
    )


# Pydantic v2 错误类型 → 中文片段映射。
# 片段会与字段中文描述（或回退的「该参数」）拼接，例如：
#   有描述："{description}{zh}"  → "用户名必须为整数"
#   无描述："该参数{zh}"         → "该参数必须为整数"
# 因此片段需同时能与「字段中文描述」和「该参数」自然搭配，避免中英文混合。
PYDANTIC_ERROR_ZH: Dict[str, str] = {
    # 必填 / 缺失
    "missing": "为必填项，不能为空",
    "missing_argument": "为必填项，不能为空",
    "missing_position_argument": "缺少必要的参数",
    "unexpected_position_argument": "存在多余的参数",
    # 字符串
    "string_type": "必须为字符串",
    "string_too_short": "长度过短",
    "string_too_long": "长度超出限制",
    "string_pattern_mismatch": "格式不正确",
    "string_substring": "包含不允许的内容",
    # 整数
    "int_type": "必须为整数",
    "int_parsing": "必须为整数",
    "int_parsing_size": "数值超出范围",
    "int_from_float": "必须为整数",
    "int_float_exact": "必须为整数",
    # 浮点数
    "float_type": "必须为数字",
    "float_parsing": "必须为数字",
    "float_number_gt": "数值过小",
    "float_number_ge": "数值过小",
    "float_number_lt": "数值过大",
    "float_number_le": "数值过大",
    # 布尔
    "bool_type": "必须为布尔值",
    "bool_parsing": "必须为布尔值",
    # 集合 / 容器
    "list_type": "必须为列表",
    "tuple_type": "必须为元组",
    "set_type": "必须为集合",
    "frozenset_type": "必须为冻结集合",
    "dict_type": "必须为对象",
    "mapping_type": "必须为对象",
    "too_short": "数量过少",
    "too_long": "数量超出限制",
    # 日期时间
    "date_type": "必须为日期",
    "date_parsing": "日期格式不正确",
    "date_object": "必须为日期",
    "date_from_datetime": "必须为日期",
    "date_from_datetime_inexact": "必须为日期",
    "datetime_type": "必须为日期时间",
    "datetime_parsing": "日期时间格式不正确",
    "datetime_object": "必须为日期时间",
    "time_type": "必须为时间",
    "time_parsing": "时间格式不正确",
    "time_object": "必须为时间",
    "timedelta_type": "必须为时间跨度",
    "timedelta_parsing": "时间跨度格式不正确",
    # UUID / URL
    "uuid_type": "必须为 UUID",
    "uuid_parsing": "UUID 格式不正确",
    "uuid_version": "UUID 版本不正确",
    "url_type": "必须为 URL",
    "url_parsing": "URL 格式不正确",
    "url_scheme": "URL 协议不正确",
    # 枚举 / 字面量
    "enum": "取值不合法",
    "literal_error": "取值不合法",
    # 数值约束
    "greater_than": "数值过小",
    "greater_than_equal": "数值过小",
    "less_than": "数值过大",
    "less_than_equal": "数值过大",
    "multiple_of": "数值不符合要求",
    "finite_number": "必须为有限数值",
    # 字节 / Decimal / 复数
    "bytes_type": "必须为字节",
    "bytes_too_short": "长度过短",
    "bytes_too_long": "长度超出限制",
    "decimal_type": "必须为数字",
    "decimal_parsing": "数字格式不正确",
    "complex_type": "必须为复数",
    "complex_parsing": "复数格式不正确",
    # 模型 / 结构
    "model_type": "必须为对象",
    "model_attributes_type": "必须为对象",
    "model_class_type": "必须为模型类型",
    "dataclass_type": "必须为数据类",
    "dataclass_exact_type": "必须为数据类",
    "arguments_type": "参数类型不合法",
    # 额外字段
    "extra_forbidden": "存在不允许的字段",
    # JSON
    "json_type": "必须为 JSON",
    "json_invalid": "JSON 格式不正确",
    "json_invalid_utf8": "JSON 编码不正确",
    # 联合类型 / 判别
    "union_tag_invalid": "取值不合法",
    "union_tag_not_found": "取值不合法",
    "discriminated_union_missing_discriminator": "缺少必要的类型标识",
    "discriminated_union_invalid_discriminator": "类型标识不合法",
    # 递归
    "recursion_loop": "存在循环引用",
}


def _ctx_fragment(error_type: str, ctx: Optional[Dict[str, Any]]) -> Optional[str]:
    """优先根据校验上下文 ctx 生成更精确的中文片段；未命中返回 None。"""
    if not ctx:
        return None
    try:
        if error_type == "greater_than" and "gt" in ctx:
            return f"必须大于 {ctx['gt']}"
        if error_type == "greater_than_equal" and "ge" in ctx:
            return f"必须大于等于 {ctx['ge']}"
        if error_type == "less_than" and "lt" in ctx:
            return f"必须小于 {ctx['lt']}"
        if error_type == "less_than_equal" and "le" in ctx:
            return f"必须小于等于 {ctx['le']}"
        if error_type == "multiple_of" and "multiple_of" in ctx:
            return f"必须是 {ctx['multiple_of']} 的倍数"
        if error_type in ("string_too_short", "too_short", "bytes_too_short") and "min_length" in ctx:
            return f"长度不能少于 {ctx['min_length']}"
        if error_type in ("string_too_long", "too_long", "bytes_too_long") and "max_length" in ctx:
            return f"长度不能超过 {ctx['max_length']}"
    except Exception:
        return None
    return None


def _model_from_annotation(annotation: Any) -> Optional[type]:
    """从类型注解中提取 Pydantic BaseModel 子类，穿透 list/Union/Optional 等容器。"""
    if annotation is None:
        return None
    origin = get_origin(annotation)
    if origin in (list, set, tuple, frozenset, dict):
        for arg in get_args(annotation):
            model = _model_from_annotation(arg)
            if model is not None:
                return model
        return None
    if origin is Union or origin is getattr(types, "UnionType", None):
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            model = _model_from_annotation(arg)
            if model is not None:
                return model
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _description_in_model(model_cls: Any, path) -> Optional[str]:
    """沿字段路径 path 递归钻取 model，返回最深层字段的中文描述（description，回退 title）。"""
    if not path:
        return None
    if not (isinstance(model_cls, type) and issubclass(model_cls, BaseModel)):
        return None
    try:
        field_info = model_cls.model_fields.get(path[0])
    except Exception:
        return None
    if field_info is None:
        return None
    if len(path) == 1:
        return field_info.description or field_info.title or None
    return _description_in_model(
        _model_from_annotation(field_info.annotation), path[1:]
    )


# FastAPI 请求参数种类 → Dependant 上的属性名映射
_PARAM_CONTAINERS = {
    "body": "body_params",
    "query": "query_params",
    "path": "path_params",
    "header": "header_params",
    "cookie": "cookie_params",
}


def _resolve_field_label(request: Optional[Request], loc) -> Optional[str]:
    """根据错误 loc 反射出字段/参数的中文描述；失败返回 None（由调用方回退为「该参数」）。

    - body：从请求体 model 的 model_fields 沿 loc 递归取 description
    - query/path/header/cookie：按参数名匹配，取 FieldInfo.description
    - 全程异常均吞掉，确保校验错误处理本身不会再次抛错
    """
    if request is None or not loc:
        return None
    try:
        kind = loc[0]
        tail = [str(x) for x in loc[1:]]
        if not tail:
            return None
        route = request.scope.get("route")
        dependant = getattr(route, "dependant", None) if route is not None else None
        if dependant is None:
            return None

        if kind == "body":
            body_params = getattr(dependant, "body_params", None) or []
            if not body_params:
                return None
            # 单 body 参数：tail 直接对应 model 字段路径
            first = body_params[0]
            desc = _description_in_model(getattr(first, "type_", None), tail)
            if desc:
                return desc
            # 多 body / embed 场景：tail[0] 可能是参数名，按名定位后再钻取
            if len(tail) > 1:
                for param in body_params:
                    if str(getattr(param, "name", "")) == tail[0]:
                        return _description_in_model(
                            getattr(param, "type_", None), tail[1:]
                        )
            return None

        container_attr = _PARAM_CONTAINERS.get(str(kind))
        if not container_attr:
            return None
        name = tail[0]
        for param in getattr(dependant, container_attr, None) or []:
            if str(getattr(param, "name", "")) == name:
                field_info = getattr(param, "field_info", None)
                if field_info is not None:
                    return getattr(field_info, "description", None) or getattr(
                        field_info, "title", None
                    )
        return None
    except Exception:
        return None


def _translate_validation_error(request: Optional[Request], error: dict) -> str:
    """将单个 Pydantic 校验错误翻译为纯中文消息（避免中英文字段名混合）。

    优先级：
      1. 自定义 validator 抛出的 ValueError/AssertionError：沿用其原始（通常为中文）消息
      2. 字段中文描述 + 中文错误片段：如「用户名必须为整数」
      3. 无描述时回退「该参数 + 片段」：如「该参数必须为整数」
    """
    loc = error.get("loc", []) or []
    error_type = error.get("type", "")
    ctx = error.get("ctx") or {}

    # 1. 自定义校验器的原始消息优先（项目内通常已是中文）
    if error_type in ("value_error", "assertion_error"):
        inner = ctx.get("error")
        if inner is not None:
            return str(inner)

    # 2. 解析中文片段：ctx 精确优先 → 映射表 → 兜底「不合法」
    zh = (
        _ctx_fragment(error_type, ctx)
        or PYDANTIC_ERROR_ZH.get(error_type)
        or "不合法"
    )

    label = _resolve_field_label(request, loc)
    return f"{label}{zh}" if label else f"该参数{zh}"


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    """
    请求参数验证异常处理器（统一返回中文消息）
    """
    request_id = get_request_trace_id(request)
    # 只取第一条错误并翻译为中文
    errors = []
    for error in exc.errors():
        errors.append(_translate_validation_error(request, error))
        break
    # 记录日志
    logger.warning(
        f"请求参数验证失败: path={request.url.path}, method={request.method}, "
        f"errors={errors}, request_id={request_id}"
    )
    # 构建响应
    response = ResponseModel(
        code=StandardResponseCode.HTTP_422,
        msg=errors[0] if errors else "请求参数验证失败",
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=StandardResponseCode.HTTP_422, content=response.model_dump()
    )


async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> ORJSONResponse:
    """
    Pydantic模型验证异常处理器
    """
    request_id = get_request_trace_id(request)
    # 格式化验证错误信息（纯中文，避免字段名与英文消息混合）
    errors = [_translate_validation_error(None, error) for error in exc.errors()]
    # 记录日志
    logger.warning(
        f"模型验证失败: path={request.url.path}, method={request.method}, "
        f"errors={errors}, request_id={request_id}"
    )
    # 构建响应
    response = ResponseModel(
        code=StandardResponseCode.HTTP_422,
        msg="数据验证失败",
        data={"errors": errors},
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=StandardResponseCode.HTTP_422, content=response.model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）
    """
    request_id = get_request_trace_id(request)
    # 记录详细错误日志（包括堆栈信息）
    logger.error(
        f"未捕获的异常: path={request.url.path}, method={request.method}, "
        f"exception_type={type(exc).__name__}, message={str(exc)}, "
        f"request_id={request_id}\n{traceback.format_exc()}"
    )
    # 构建响应
    response = ResponseModel(
        code=StandardResponseCode.HTTP_500,
        msg="服务器内部错误",
        request_id=request_id,
    )
    return ORJSONResponse(
        status_code=StandardResponseCode.HTTP_500, content=response.model_dump()
    )
