#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""租户选择/切换接口"""

import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.config import settings
from core.redis import get_redis_util
from core.response.response_schema import ResponseModel
from core.exception.errors import NotFoundError, ForbiddenError
from core.security.oauth.user_manager import base_user_manager, build_session_key
from core.security.oauth.jwt import JWTAuthManager
from app.models.sys.user import SysUser
from modules.admin.deps.auth.user_manager import current_user
from plugins.multi_tenant.services.tenant_service import TenantService
from plugins.multi_tenant.schemas.tenant import SelectTenantRequest

logger = logging.getLogger(__name__)

tenant_auth_router = APIRouter(prefix="/auth", tags=["租户认证"])


@tenant_auth_router.post(
    "/select-tenant",
    response_model=ResponseModel,
    summary="选择/切换租户",
    description="用户选择一个租户后，返回包含 tenant_id 的新 JWT token",
)
async def select_tenant(
    req: SelectTenantRequest,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """选择或切换租户，返回新 token"""
    # 验证用户属于该租户
    tenants = await TenantService.get_user_tenants(db, user.id)
    target = None
    for t in tenants:
        if t.id == req.tenant_id:
            target = t
            break

    if not target:
        raise ForbiddenError(msg="您不属于该租户")

    if not target.status:
        raise ForbiddenError(msg="该租户已被禁用")

    # 创建包含 tenant_id 的新 token
    tokens = await base_user_manager.create_token(
        user_id=user.id,
        user_role="admin",
        username=user.username,
        tenant_id=target.id,
    )

    # 重新编码，加入 tenant_id
    extra_claims = {"tenant_id": str(target.id)}

    access_data = JWTAuthManager.decode_token(tokens.access_token)
    access_data.update(extra_claims)
    # 移除标准 JWT 字段让 create_access_token 重新生成
    for k in ("exp", "iat", "aud", "iss"):
        access_data.pop(k, None)
    new_access = JWTAuthManager.create_access_token(access_data)

    refresh_data = JWTAuthManager.decode_token(tokens.refresh_token)
    refresh_data.update(extra_claims)
    for k in ("exp", "iat", "aud", "iss", "type"):
        refresh_data.pop(k, None)
    new_refresh = JWTAuthManager.create_refresh_token(refresh_data)

    from core.security.oauth.jwt import Token

    new_tokens = Token(
        access_token=new_access,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=new_refresh,
    )

    return ResponseModel(
        data=new_tokens.model_dump(),
        msg=f"已切换到租户: {target.name}",
    )
