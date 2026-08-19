#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from .endpoints import voice_consultation_session_router

router = APIRouter(prefix="/voice-consultation")

router.include_router(voice_consultation_session_router)
