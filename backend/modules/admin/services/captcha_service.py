#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""滑块验证码服务。

使用 Pillow 从预设背景图中裁剪拼图块，答案存 Redis，
验证通过后发放单次有效的 captcha_token。
"""

import base64
import io
import logging
import random
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from core.config import settings
from core.redis import RedisPool
from core.security.rate_limit import LOGIN_FAIL_KEY_PREFIX
from core.security.rate_limit_config import RateLimitConfigProvider

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static" / "captcha"
PUZZLE_SIZE = 44
PROTRUSION_R = 11
CAPTCHA_WIDTH = 350
CAPTCHA_HEIGHT = 200


class CaptchaService:
    """滑块验证码业务逻辑"""

    @staticmethod
    async def generate_captcha():
        """生成滑块拼图验证码，返回 CaptchaImageData 对应的 dict。"""
        # 1. 随机选背景图
        bg_dir = _STATIC_DIR / "backgrounds"
        bg_files = list(bg_dir.glob("*.png"))
        if not bg_files:
            # 没有预设图片时用纯色渐变兜底
            bg_img = _generate_fallback_background()
        else:
            bg_img = Image.open(random.choice(bg_files)).convert("RGBA")
            bg_img = bg_img.resize((CAPTCHA_WIDTH, CAPTCHA_HEIGHT), Image.LANCZOS)

        # 2. 随机确定拼图块位置
        mask_img = Image.open(_STATIC_DIR / "mask.png").convert("L")
        mask_w, mask_h = mask_img.size

        answer_x = random.randint(60, CAPTCHA_WIDTH - mask_w - 10)
        answer_y = random.randint(10, CAPTCHA_HEIGHT - mask_h - 10)

        # 3. 从背景中裁剪拼图块（用 mask 做透明遮罩）
        bg_for_piece = bg_img.crop((answer_x, answer_y, answer_x + mask_w, answer_y + mask_h))
        piece_img = Image.new("RGBA", (mask_w, mask_h), (0, 0, 0, 0))
        piece_img.paste(bg_for_piece, mask=mask_img)
        # 加边框让拼图块更清晰
        piece_bordered = _add_piece_border(piece_img, mask_img)

        # 4. 在背景图上画缺口
        overlay = Image.new("RGBA", (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.bitmap((answer_x, answer_y), mask_img, fill=(0, 0, 0, 90))
        bg_img = Image.alpha_composite(bg_img, overlay)

        # 5. 转 base64
        bg_b64 = _img_to_base64(bg_img.convert("RGB"), "PNG")
        piece_b64 = _img_to_base64(piece_bordered, "PNG")

        # 6. 存 Redis
        captcha_id = str(uuid.uuid4())
        ttl = await RateLimitConfigProvider.get(
            "rate_limit.captcha_token_ttl", settings.RATE_LIMIT.CAPTCHA_TOKEN_TTL
        )
        redis_client = RedisPool.get_client()
        key = f"captcha:id:{captcha_id}"
        async with redis_client.pipeline() as pipe:
            pipe.hset(key, "answer_x", str(answer_x))
            pipe.hset(key, "attempts", "0")
            pipe.expire(key, ttl)
            await pipe.execute()

        from modules.admin.schemas.captcha import CaptchaImageData

        return CaptchaImageData(
            captcha_id=captcha_id,
            background_image=bg_b64,
            puzzle_image=piece_b64,
            puzzle_y=answer_y,
            slider_width=CAPTCHA_WIDTH,
        )

    @staticmethod
    async def verify_captcha(captcha_id: str, slide_x: int) -> str:
        """验证滑块位置，成功返回 captcha_token，失败抛 CustomError。"""
        from core.exception.errors import CustomError, CustomErrorCode

        redis_client = RedisPool.get_client()
        key = f"captcha:id:{captcha_id}"

        exists = await redis_client.exists(key)
        if not exists:
            raise CustomError(error=CustomErrorCode.CAPTCHA_INVALID)

        answer_x_raw = await redis_client.hget(key, "answer_x")
        if answer_x_raw is None:
            raise CustomError(error=CustomErrorCode.CAPTCHA_INVALID)
        answer_x = int(answer_x_raw)

        tolerance = await RateLimitConfigProvider.get(
            "rate_limit.captcha_tolerance", settings.RATE_LIMIT.CAPTCHA_TOLERANCE
        )
        max_attempts = await RateLimitConfigProvider.get(
            "rate_limit.captcha_max_verify_attempts", settings.RATE_LIMIT.CAPTCHA_MAX_VERIFY_ATTEMPTS
        )

        # 增加尝试次数
        attempts = await redis_client.hincrby(key, "attempts", 1)

        if abs(slide_x - answer_x) > tolerance:
            if attempts >= max_attempts:
                await redis_client.delete(key)
            raise CustomError(error=CustomErrorCode.CAPTCHA_VERIFY_FAILED)

        # 验证通过，生成 token
        token = str(uuid.uuid4())
        ttl = await RateLimitConfigProvider.get(
            "rate_limit.captcha_token_ttl", settings.RATE_LIMIT.CAPTCHA_TOKEN_TTL
        )
        await redis_client.set(f"captcha:token:{token}", "", ex=ttl)
        await redis_client.delete(key)

        return token

    @staticmethod
    async def validate_captcha_token(token: str) -> bool:
        """校验并消费 captcha_token。"""
        if not token:
            return False
        redis_client = RedisPool.get_client()
        key = f"captcha:token:{token}"
        exists = await redis_client.exists(key)
        if exists:
            await redis_client.delete(key)
        return bool(exists)

    @staticmethod
    async def get_failure_count(ip: str) -> int:
        """读取当前 IP 的登录失败次数。"""
        if not ip:
            return 0
        redis_client = RedisPool.get_client()
        val = await redis_client.get(f"{LOGIN_FAIL_KEY_PREFIX}{ip}")
        return int(val) if val else 0


def _img_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


def _add_piece_border(piece: Image.Image, mask: Image.Image) -> Image.Image:
    """给拼图块加白色描边以增强可见性。"""
    # 稍微膨胀 mask，取差集作为边框区域
    from PIL import ImageChops
    dilated = mask.filter(ImageFilter.MaxFilter(3))
    border = ImageChops.subtract(dilated, mask)
    border_layer = Image.new("RGBA", piece.size, (0, 0, 0, 0))
    border_layer.paste((255, 255, 255, 160), mask=border)
    return Image.alpha_composite(piece, border_layer)


def _generate_fallback_background() -> Image.Image:
    """没有预设背景图时生成一张渐变背景。"""
    img = Image.new("RGBA", (CAPTCHA_WIDTH, CAPTCHA_HEIGHT))
    draw = ImageDraw.Draw(img)
    import random as _r

    r1, g1, b1 = _r.randint(60, 180), _r.randint(60, 180), _r.randint(60, 180)
    r2, g2, b2 = _r.randint(60, 180), _r.randint(60, 180), _r.randint(60, 180)
    for y in range(CAPTCHA_HEIGHT):
        t = y / CAPTCHA_HEIGHT
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (CAPTCHA_WIDTH, y)], fill=(r, g, b, 255))
    return img
