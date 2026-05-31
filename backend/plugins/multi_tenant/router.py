#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter
from .endpoints.tenant import tenant_router
from .endpoints.auth import tenant_auth_router

router = APIRouter(prefix="/admin/sys")
router.include_router(tenant_router)
router.include_router(tenant_auth_router)
