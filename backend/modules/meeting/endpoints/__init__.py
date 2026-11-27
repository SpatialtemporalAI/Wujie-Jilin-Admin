#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .agent import agent_meeting_router
from .minutes import minutes_router
from .voiceprint import voiceprint_router

__all__ = ["agent_meeting_router", "minutes_router", "voiceprint_router"]
