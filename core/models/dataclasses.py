#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dataclasses

from datetime import datetime


@dataclasses.dataclass
class SnowflakeInfo:
    timestamp: int
    datetime: str
    cluster_id: int
    node_id: int
    sequence: int
