#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import event, or_
from sqlalchemy.orm import Session, with_loader_criteria

from plugins.multi_tenant.deps.tenant_context import get_current_tenant_id


# ---- 注册表 ----

_strict_models: set = set()  # 严格隔离：tenant_id == current_tenant_id
_optional_models: set = set()  # 可选隔离：tenant_id == current_tenant_id OR tenant_id IS NULL


def register_tenant_strict(model_cls) -> None:
    """注册模型为严格租户隔离（查询只返回当前租户数据）"""
    _strict_models.add(model_cls)


def register_tenant_optional(model_cls) -> None:
    """注册模型为可选租户隔离（查询返回当前租户 + 全局数据）"""
    _optional_models.add(model_cls)


def is_tenant_model(model_cls) -> bool:
    """检查模型是否已注册租户隔离"""
    return model_cls in _strict_models or model_cls in _optional_models


def get_all_tenant_models() -> set:
    """获取所有已注册的租户隔离模型"""
    return _strict_models | _optional_models


# ---- 过滤插件 ----

def setup_tenant_filter_plug() -> None:
    """注册自动租户过滤事件监听"""

    @event.listens_for(Session, "do_orm_execute")
    def _add_tenant_filtering(execute_state):
        """
        自动为查询添加租户过滤条件。
        仅当 tenant_id_ctx 有值时生效。
        使用 execution_options(ignore_tenant=True) 可跳过过滤。
        """
        if (
            not execute_state.is_select
            or execute_state.is_column_load
            or execute_state.is_relationship_load
            or execute_state.execution_options.get("ignore_tenant", False)
        ):
            return

        current_tenant_id = get_current_tenant_id()
        if current_tenant_id is None:
            return

        # 严格隔离：tenant_id == current_tenant_id
        for model_cls in _strict_models:
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    model_cls,
                    lambda cls: cls.tenant_id == current_tenant_id,
                    include_aliases=True,
                )
            )

        # 可选隔离：tenant_id == current_tenant_id OR tenant_id IS NULL
        for model_cls in _optional_models:
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    model_cls,
                    lambda cls: or_(
                        cls.tenant_id == current_tenant_id,
                        cls.tenant_id.is_(None),
                    ),
                    include_aliases=True,
                )
            )

    @event.listens_for(Session, "before_flush")
    def _inject_tenant_id(session, flush_context, instances):
        """自动为新记录注入 tenant_id"""
        current_tenant_id = get_current_tenant_id()
        if current_tenant_id is None:
            return
        all_models = _strict_models | _optional_models
        for obj in session.new:
            if type(obj) in all_models:
                tid = getattr(obj, "tenant_id", None)
                if tid is None or tid == 0:
                    obj.tenant_id = current_tenant_id
