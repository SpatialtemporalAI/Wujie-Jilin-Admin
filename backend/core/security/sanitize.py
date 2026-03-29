#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

import bleach

ALLOWED_TAGS = ["b", "strong", "i", "em", "u", "p", "br", "ul", "ol", "li", "a"]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_rich_text(content: Optional[str]) -> Optional[str]:
    """对可富文本字段做白名单清洗。"""
    if content is None:
        return None
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

