#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class CaptchaVerifyRequest(BaseModel):
    """滑块验证请求"""

    captcha_id: str = Field(..., description="验证码ID")
    slide_x: int = Field(..., description="滑块X坐标位置(像素)")


class CaptchaImageData(BaseModel):
    """验证码图片数据"""

    captcha_id: str = Field(..., description="验证码ID")
    background_image: str = Field(..., description="背景图(base64 data URL)")
    puzzle_image: str = Field(..., description="拼图块(base64 data URL)")
    puzzle_y: int = Field(..., description="拼图块Y坐标(像素)")
    slider_width: int = Field(..., description="滑动条宽度(像素)")


class CaptchaVerifyResponse(BaseModel):
    """滑块验证成功响应"""

    captcha_token: str = Field(..., description="验证码令牌(单次有效)")


class CaptchaCheckResponse(BaseModel):
    """验证码需求检查响应"""

    required: bool = Field(..., description="是否需要验证码")
    fail_count: int = Field(..., description="当前IP登录失败次数")
