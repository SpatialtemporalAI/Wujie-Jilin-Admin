#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .merchant import merchant_router
from .openapi import openapi_router

__all__ = ["merchant_router", "openapi_router"]
