#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从数据库读取 SceneMap + SceneMapAnnotation，按 proto NotifyMapSaved 协议
组装为 JSON 并打印；加 --send 才会真正调 gRPC 推送。

字段映射规则与 backend/modules/grpc/converter.py 保持一致：
- id / version / labels[].id 均为 str
- image_url: 完整可访问 URL（HMAC 签名 + 时效），启用签名模式后形如：
  {SERVICE.BASE_URL}/admin/sys/file/{file_id}/preview?expires=<unix>&sig=<hex>
  nav_image_id 优先，fallback image_id；都没有则空串
- origin_x/y = SceneMap.start_point_x/y
- resolution = SceneMap.resolution
- labels 由 scene_map_annotation 映射

用法示例：
    # 仅导出 JSON
    python scripts/dump_notify_map_saved.py --map-id 12

    # 写到文件
    python scripts/dump_notify_map_saved.py --map-id 12 --out notify.json

    # 真实发送 gRPC
    python scripts/dump_notify_map_saved.py --map-id 12 --send
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# 让脚本可以独立运行：把 backend/ 加入 sys.path
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

# 默认走 dev 环境，与 settings 加载逻辑一致
os.environ.setdefault("ENVIR", "dev")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from core.config import settings  # noqa: E402
from database.models.business.scene_map import SceneMap  # noqa: E402
from database.models.business.scene_map_annotation import SceneMapAnnotation  # noqa: E402
from database.models.sys.file import SysFile  # noqa: E402


def build_sync_db_url() -> str:
    """从 settings 构造同步驱动 DSN（psycopg2）"""
    db = settings.DATABASE
    pwd = db.password or ""
    return (
        f"postgresql+psycopg2://{db.username}:{pwd}@{db.host}:{db.port}/{db.database}"
    )


def build_image_url(file_id: int | None) -> str:
    """与 FileService.get_file_url 等价：返回签名 URL（启用签名模式时）"""
    if not file_id:
        return ""
    from core.security.file_signature import build_signed_url, is_enabled

    if is_enabled():
        return build_signed_url(file_id)
    base_url = (settings.SERVICE.BASE_URL or "").rstrip("/")
    return f"{base_url}/admin/sys/file/{file_id}/preview"


def load_map_payload(engine, map_id: int) -> dict[str, Any]:
    """读取数据库并组装为 NotifyMapSavedRequest 的 JSON 字典"""
    Session = sessionmaker(bind=engine)
    with Session() as session:
        map_obj = session.execute(
            select(SceneMap).where(
                SceneMap.id == map_id,
                SceneMap.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if map_obj is None:
            raise SystemExit(f"地图 id={map_id} 不存在或已删除")

        # nav_image_id 优先，fallback image_id
        nav_file_id = map_obj.nav_image_id or map_obj.image_id
        if nav_file_id:
            exists = session.execute(
                select(SysFile.id).where(
                    SysFile.id == nav_file_id,
                    SysFile.deleted_at.is_(None),
                )
            ).first()
            image_url = build_image_url(nav_file_id) if exists else ""
        else:
            image_url = ""

        annotations = list(
            session.execute(
                select(SceneMapAnnotation)
                .where(SceneMapAnnotation.map_id == map_id)
                .order_by(SceneMapAnnotation.id.asc())
            )
            .scalars()
            .all()
        )

        labels = [
            {
                "id": str(a.id),
                "name": a.name,
                "type": a.type,
                "x": float(a.x),
                "y": float(a.y),
                "angle": float(a.angle or 0),
            }
            for a in annotations
        ]

        return {
            "map_info": {
                "id": str(map_obj.id),
                "version": str(map_obj.version or 0),
                "map": {
                    "image_url": image_url,
                    "resolution": float(map_obj.resolution or 1),
                    "origin_x": float(map_obj.start_point_x or 0),
                    "origin_y": float(map_obj.start_point_y or 0),
                },
                "labels": labels,
            }
        }


async def send_via_grpc(
    payload: dict[str, Any], map_id: int, grpc_addr: str | None
) -> None:
    """通过 MapServiceClient 推送（按 robot.middleware 广播）"""
    from app.grpc.generated.map import map_pb2
    from modules.grpc.addr_provider import get_config_addr_provider
    from modules.grpc.client import MapServiceClient

    info = payload["map_info"]
    meta = info["map"]
    map_info = map_pb2.MapInfo(
        id=info["id"],
        version=info["version"],
        map=map_pb2.MapMeta(
            image_url=meta["image_url"],
            resolution=meta["resolution"],
            origin_x=meta["origin_x"],
            origin_y=meta["origin_y"],
        ),
        labels=[
            map_pb2.MapLabel(
                id=l["id"],
                name=l["name"],
                type=l["type"],
                x=l["x"],
                y=l["y"],
                angle=l["angle"],
            )
            for l in info["labels"]
        ],
    )

    if grpc_addr:
        # 手动指定地址，跳过 DB 反查（调试用）
        targets: list[tuple[int, str]] = [(0, grpc_addr)]
    else:
        targets = await get_config_addr_provider().find_addrs_by_target_and_map(
            "middleware", map_id
        )

    print(f"---- targets ({len(targets)}) ----")
    for rid, addr in targets:
        print(f"robot_id={rid} addr={addr}")

    resp = await MapServiceClient.notify_map_saved(map_info, targets)
    print("---- gRPC response ----")
    print(f"status:  {resp.status}")
    print(f"message: {resp.message}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="生成 / 发送 NotifyMapSaved 报文")
    p.add_argument("--map-id", type=int, required=True, help="场景地图 ID")
    p.add_argument("--out", type=str, default=None, help="写入 JSON 文件路径；不传则打印到 stdout")
    p.add_argument(
        "--send",
        action="store_true",
        help="真正调用 MapService.NotifyMapSaved 推送（需 settings.GRPC.ENABLED=true）",
    )
    p.add_argument(
        "--grpc-addr",
        type=str,
        default=None,
        help="手动指定推送目标地址 host:port，跳过按 robot.middleware 反查（调试用）",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    engine = create_engine(build_sync_db_url(), echo=False, future=True)
    try:
        payload = load_map_payload(engine, args.map_id)
    finally:
        engine.dispose()

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print("---- NotifyMapSavedRequest (JSON) ----")
        print(rendered)

    if args.send:
        asyncio.run(send_via_grpc(payload, args.map_id, args.grpc_addr))


if __name__ == "__main__":
    main()
