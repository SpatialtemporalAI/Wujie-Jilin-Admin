#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from plugins.multi_tenant.models.tenant_mixin import TenantMixin
from plugins.multi_tenant.deps.tenant_context import get_current_tenant_id


def setup_tenant_filter_plug() -> None:
    """注册自动租户过滤事件监听，与软删除插件同构"""

    @event.listens_for(Session, "do_orm_execute")
    def _add_tenant_filtering(execute_state):
        """
        自动为查询添加租户过滤条件。
        仅当 tenant_id_ctx 有值时生效。
        使用 execution_options(ignore_tenant=True) 可跳过过滤。
        """
        if (
            execute_state.is_select
            and not execute_state.is_column_load
            and not execute_state.is_relationship_load
            and not execute_state.execution_options.get("ignore_tenant", False)
        ):
            current_tenant_id = get_current_tenant_id()
            if current_tenant_id is not None:
                execute_state.statement = execute_state.statement.options(
                    with_loader_criteria(
                        TenantMixin,
                        lambda cls: cls.tenant_id == current_tenant_id,
                        include_aliases=True,
                    )
                )

    @event.listens_for(Session, "before_flush")
    def _inject_tenant_id(session, flush_context, instances):
        """自动为新记录注入 tenant_id"""
        current_tenant_id = get_current_tenant_id()
        if current_tenant_id is None:
            return
        for obj in session.new:
            if isinstance(obj, TenantMixin) and obj.tenant_id == 0:
                obj.tenant_id = current_tenant_id
