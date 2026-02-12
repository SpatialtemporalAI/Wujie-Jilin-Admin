#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from database.db_manager import get_session
from core.response.response_schema import ResponseModel, ResponsePageModel
from app.models.common.page import PageRequest, get_page_params, get_paginated_results

from app.models.sys.user import SysUser
from modules.admin.services.sys import UserService
from modules.admin.models.sys.user import SysUserResponseData


# 修改密码请求模型
class ChangePasswordRequest(BaseModel):
    """
    修改密码请求模型
    """

    new_password: str


# 创建用户管理路由
user_router = APIRouter(prefix="/user", tags=["用户管理"])


@user_router.get("/list", response_model=ResponsePageModel[SysUserResponseData])
async def get_user_list(
    page_params: PageRequest = Depends(get_page_params),
    status: Optional[str] = Query(None, description="状态"),
    username: Optional[str] = Query(None, description="用户名"),
    nickname: Optional[str] = Query(None, description="昵称"),
    phone: Optional[str] = Query(None, description="手机号"),
    email: Optional[str] = Query(None, description="邮箱"),
    isSuperuser: Optional[str] = Query(None, description="是否为超级管理员"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取用户列表
    """

    # 处理布尔类型参数
    def parse_bool_param(value: Optional[str]) -> Optional[bool]:
        if value is None or value == "":
            return None
        if value.lower() in ("true", "1", "yes", "y"):
            return True
        if value.lower() in ("false", "0", "no", "n"):
            return False
        return None

    status_bool = parse_bool_param(status)
    is_superuser_bool = parse_bool_param(isSuperuser)

    # 获取查询语句
    stmt = await UserService.get_user_list(
        status=status_bool,
        username=username,
        nickname=nickname,
        phone=phone,
        email=email,
        is_superuser=is_superuser_bool,
    )

    # 获取分页结果
    result = await get_paginated_results(
        db=db, page_params=page_params, query=stmt, schema=SysUserResponseData
    )

    # 返回分页结果
    return ResponsePageModel(data=result)


@user_router.get("/{user_id}", response_model=ResponseModel[SysUserResponseData])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个用户
    """
    user = await UserService.get_user(db, user_id)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.post("", response_model=ResponseModel[SysUserResponseData])
async def create_user(
    user: SysUser,
    db: AsyncSession = Depends(get_session),
):
    """
    创建用户
    """
    user = await UserService.create_user(db, user)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.put("/{user_id}", response_model=ResponseModel[SysUserResponseData])
async def update_user(
    user_id: int, user: SysUser, db: AsyncSession = Depends(get_session)
):
    """
    更新用户
    """
    user = await UserService.update_user(db, user_id, user)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.post("/{user_id}/roles", response_model=ResponseModel)
async def assign_role_to_user(
    user_id: int, role_ids: List[int], db: AsyncSession = Depends(get_session)
):
    """
    为用户分配角�?"""
    await UserService.assign_role_to_user(db, user_id, role_ids)
    return ResponseModel(msg="分配成功")


@user_router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除用户
    """
    await UserService.delete_user(db, user_id)
    return ResponseModel(msg="删除成功")


@user_router.put("/{user_id}/password", response_model=ResponseModel)
async def change_user_password(
    user_id: int,
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    修改用户密码
    """
    await UserService.change_password(db, user_id, request.new_password)
    return ResponseModel(msg="密码修改成功")
