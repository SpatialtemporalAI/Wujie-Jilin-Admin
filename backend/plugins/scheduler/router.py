#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from plugins.scheduler.endpoints.scheduled_task import scheduler_task_router
from plugins.scheduler.endpoints.task_log import scheduler_log_router

router = APIRouter(prefix="/admin/sys")
router.include_router(scheduler_task_router)
router.include_router(scheduler_log_router)
