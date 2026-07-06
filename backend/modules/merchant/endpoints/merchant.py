#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户管理接口（后台，JWT 鉴权 + 权限校验）
"""
import logging

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from database.models.sys.user import SysUser
from core.response.response_schema import ResponseModel, ResponsePageModel
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.decorators.operation_log import log_operation
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission

from modules.merchant.services.merchant_service import MerchantService
from modules.merchant.schemas.merchant import (
    MerchantQueryParams,
    MerchantCreate,
    MerchantUpdate,
    MerchantRobotBind,
    MerchantStatusUpdate,
    MerchantListResponse,
    MerchantDetailResponse,
    MerchantCreateResponse,
    MerchantApiKeyResetResponse,
)

logger = logging.getLogger(__name__)

merchant_router = APIRouter(
    prefix="/merchant",
    tags=["商户管理"],
    dependencies=[Depends(current_user)],
)


@merchant_router.get(
    "/list",
    response_model=ResponsePageModel[MerchantListResponse],
    dependencies=[Depends(require_permission("merchant:list"))],
)
async def get_merchant_list(
    page_params: PageRequest = Depends(get_page_params),
    query_params: MerchantQueryParams = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """获取商户列表"""
    query_params.page = page_params.page
    query_params.page_size = page_params.page_size
    query = MerchantService.build_list_query(query_params)
    page_data = await get_paginated_results(
        db=db, page_params=page_params, query=query, schema=MerchantListResponse
    )
    return ResponsePageModel[MerchantListResponse](data=page_data)


@merchant_router.get(
    "/{merchant_id}",
    response_model=ResponseModel[MerchantDetailResponse],
    dependencies=[Depends(require_permission("merchant:list"))],
)
async def get_merchant(
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
):
    """获取商户详情（含绑定机器人ID）"""
    merchant = await MerchantService.get(db, merchant_id)
    resp = MerchantDetailResponse.model_validate(merchant)
    resp.robot_ids = await MerchantService.get_robot_ids(db, merchant.id)
    return ResponseModel(data=resp)


@merchant_router.post(
    "/add",
    response_model=ResponseModel[MerchantCreateResponse],
    dependencies=[Depends(require_permission("merchant:add"))],
)
@log_operation(module="merchant", action="create", description="创建商户")
async def create_merchant(
    merchant_create: MerchantCreate,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """创建商户（自动生成 api_key/api_secret，secret 仅本次返回）"""
    merchant, plaintext_secret = await MerchantService.create(db, merchant_create)
    resp = MerchantCreateResponse.model_validate(merchant)
    resp.api_secret = plaintext_secret
    return ResponseModel(data=resp, msg="创建成功，请妥善保存 API Secret（仅展示一次）")


@merchant_router.put(
    "/{merchant_id}",
    response_model=ResponseModel[MerchantDetailResponse],
    dependencies=[Depends(require_permission("merchant:edit"))],
)
@log_operation(module="merchant", action="update", description="更新商户")
async def update_merchant(
    merchant_update: MerchantUpdate,
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """更新商户"""
    merchant = await MerchantService.update(db, merchant_id, merchant_update)
    resp = MerchantDetailResponse.model_validate(merchant)
    resp.robot_ids = await MerchantService.get_robot_ids(db, merchant.id)
    return ResponseModel(data=resp, msg="更新成功")


@merchant_router.put(
    "/{merchant_id}/toggle",
    response_model=ResponseModel[MerchantDetailResponse],
    dependencies=[Depends(require_permission("merchant:edit"))],
)
@log_operation(module="merchant", action="toggle", description="切换商户状态")
async def toggle_merchant_status(
    status_update: MerchantStatusUpdate,
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """启用/禁用商户"""
    merchant = await MerchantService.get(db, merchant_id)
    merchant.status = status_update.status
    await db.commit()
    await db.refresh(merchant)
    resp = MerchantDetailResponse.model_validate(merchant)
    resp.robot_ids = await MerchantService.get_robot_ids(db, merchant.id)
    return ResponseModel(data=resp, msg="状态更新成功")


@merchant_router.post(
    "/{merchant_id}/reset-api-key",
    response_model=ResponseModel[MerchantApiKeyResetResponse],
    dependencies=[Depends(require_permission("merchant:edit"))],
)
@log_operation(module="merchant", action="reset_api_key", description="重置商户API密钥")
async def reset_merchant_api_key(
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """重置 api_key/api_secret（旧密钥立即失效，secret 仅本次返回）"""
    merchant, plaintext_secret = await MerchantService.reset_api_key(db, merchant_id)
    resp = MerchantApiKeyResetResponse.model_validate(merchant)
    resp.api_secret = plaintext_secret
    return ResponseModel(data=resp, msg="重置成功，请妥善保存新的 API Secret（仅展示一次）")


@merchant_router.put(
    "/{merchant_id}/robots",
    response_model=ResponseModel[MerchantDetailResponse],
    dependencies=[Depends(require_permission("merchant:edit"))],
)
@log_operation(module="merchant", action="bind_robots", description="绑定商户机器人")
async def bind_merchant_robots(
    bind: MerchantRobotBind,
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """绑定/解绑商户机器人（全量替换）"""
    merchant = await MerchantService.get(db, merchant_id)
    await MerchantService._replace_robots(db, merchant.id, bind.robot_ids)
    await db.refresh(merchant)
    resp = MerchantDetailResponse.model_validate(merchant)
    resp.robot_ids = await MerchantService.get_robot_ids(db, merchant.id)
    return ResponseModel(data=resp, msg="机器人绑定成功")


@merchant_router.delete(
    "/{merchant_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("merchant:delete"))],
)
@log_operation(module="merchant", action="delete", description="删除商户")
async def delete_merchant(
    merchant_id: int = Path(..., description="商户ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """删除商户（软删除）"""
    await MerchantService.delete(db, merchant_id)
    return ResponseModel(msg="删除成功")
