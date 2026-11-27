#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from .endpoints import minutes_router, voiceprint_router
from .endpoints.agent import agent_meeting_router

router = APIRouter(prefix="/meeting")

router.include_router(voiceprint_router)
router.include_router(minutes_router)

__all__ = ["router", "agent_meeting_router"]
