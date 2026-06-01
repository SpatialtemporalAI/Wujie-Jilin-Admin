#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Optional

from pydantic import BaseModel, Field


class TenantJwtConfig(BaseModel):
    """Per-tenant JWT configuration. All fields optional -- missing means 'use global'."""

    secret_key: Optional[str] = Field(
        None, min_length=16, description="JWT secret key"
    )
    algorithm: Optional[str] = Field(
        None, pattern=r"^(HS256|HS384|HS512)$", description="JWT algorithm"
    )
    access_lifetime: Optional[int] = Field(
        None, gt=0, le=86400, description="Access token lifetime (seconds)"
    )


class TenantConfigSchema(BaseModel):
    """Full JSON structure stored in tenant.config column."""

    jwt: Optional[TenantJwtConfig] = Field(None, description="JWT settings")


def parse_tenant_config(config_str: Optional[str]) -> TenantConfigSchema:
    """Parse tenant config JSON string into TenantConfigSchema."""
    if not config_str:
        return TenantConfigSchema()
    data = json.loads(config_str)
    return TenantConfigSchema.model_validate(data)


def serialize_tenant_config(config: TenantConfigSchema) -> str:
    """Serialize TenantConfigSchema to JSON string for storage."""
    return config.model_dump_json(exclude_none=True)
