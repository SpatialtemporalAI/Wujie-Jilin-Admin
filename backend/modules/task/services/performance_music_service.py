#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表演任务背景音乐：用户上传音频（mp3/wav）

规则：
- 上传音频仅自己可见、可选用、可删除（被表演任务引用的不允许删除）；
- 时长超过 4 分钟（240 秒）的音频自动截取前 4 分钟；
- performance_steps.music 中，预设为 bdj_* 标识，用户上传为 upload:<sys_file_id>。
"""
import asyncio
import logging
import re
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exception.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.storage import generate_stored_name, get_storage_backend
from database.models.business.task import Task
from database.models.sys.file import SysFile
from database.utils.timezone import timezone

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = ("mp3", "wav")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 单个音频最大 20MB
MAX_DURATION_SECONDS = 240  # 背景音乐最长 4 分钟，超出自动截取前 4 分钟
# 截取判定的容忍秒数：超出 240s 一点点（如 240.3s）不再重新转码
_DURATION_TOLERANCE = 0.5

UPLOAD_MUSIC_PREFIX = "upload:"
UPLOAD_MUSIC_PATTERN = re.compile(r"^upload:(\d+)$")

# 预设音乐对应的服务端音频文件（sys_file_id）：填入后预设曲目即可试听
# （与上传音乐一样走 /admin/sys/file/{file_id}/preview）。预设音频原本只内置在
# 机器人端，将音频文件上传到文件管理后，把对应的 sys_file_id 填到这里即可。
# 被映射的文件不会再出现在「我上传的音乐」列表中（避免重复展示）。
PRESET_MUSIC_FILE_IDS: dict[str, int] = {
    "bdj_1": 3728273413709824,  # 八段锦1.mp3
    "bdj_2": 3728273413775360,  # 八段锦2.mp3
    "bdj_3": 3728273413644288,  # 八段锦3.mp3
    # "bdj_full_12min": 暂无对应服务端音频文件
}

_DURATION_RE = re.compile(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)")


def _get_ffmpeg_exe() -> str:
    """获取 ffmpeg 可执行文件路径（imageio-ffmpeg 自带二进制，无需系统安装）"""
    try:
        import imageio_ffmpeg
    except ImportError as e:
        raise ValidationError(msg="服务端缺少 imageio-ffmpeg 依赖，无法处理音频") from e
    return imageio_ffmpeg.get_ffmpeg_exe()


def _probe_duration_file(ffmpeg: str, src: Path) -> float:
    """用 ffmpeg 探测音频文件时长（秒）；无法解析时抛 ValidationError"""
    probe = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(src)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    match = _DURATION_RE.search(probe.stderr or "")
    if not match:
        raise ValidationError(msg="无法解析音频文件，请确认是有效的 mp3/wav 音频")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _probe_duration_bytes(file_data: bytes, ext: str) -> float:
    """探测内存中音频字节的时长（秒）"""
    ffmpeg = _get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="perf_music_probe_") as tmp_dir:
        src = Path(tmp_dir) / f"src.{ext}"
        src.write_bytes(file_data)
        return _probe_duration_file(ffmpeg, src)


def _probe_and_truncate(file_data: bytes, ext: str) -> tuple[float, bytes, bool]:
    """探测音频时长，超过 4 分钟则截取前 4 分钟

    返回 (原始时长秒, 最终文件字节, 是否发生了截取)
    """
    ffmpeg = _get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="perf_music_") as tmp_dir:
        src = Path(tmp_dir) / f"src.{ext}"
        src.write_bytes(file_data)
        duration = _probe_duration_file(ffmpeg, src)

        if duration <= MAX_DURATION_SECONDS + _DURATION_TOLERANCE:
            return duration, file_data, False

        dst = Path(tmp_dir) / f"dst.{ext}"
        cut = subprocess.run(
            [ffmpeg, "-y", "-i", str(src), "-t", str(MAX_DURATION_SECONDS), "-c", "copy", str(dst)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if cut.returncode != 0 or not dst.exists():
            logger.error("音频截取失败: %s", (cut.stderr or "")[-500:])
            raise ValidationError(msg="音频截取失败，请更换音频文件后重试")
        logger.info("音频时长 %.1fs 超过 %ds，已截取前 %ds", duration, MAX_DURATION_SECONDS, MAX_DURATION_SECONDS)
        return duration, dst.read_bytes(), True


def is_upload_music(value: str) -> bool:
    """判断 music 标识是否为用户上传音频"""
    return bool(UPLOAD_MUSIC_PATTERN.match(value or ""))


def parse_upload_file_id(value: str) -> int | None:
    """从 upload:<file_id> 标识中解析 sys_file_id，非法返回 None"""
    match = UPLOAD_MUSIC_PATTERN.match(value or "")
    return int(match.group(1)) if match else None


class PerformanceMusicService:

    @staticmethod
    async def upload_music(
        db: AsyncSession,
        file_data: bytes,
        original_name: str,
        mime_type: str,
        user_id: int,
    ) -> tuple[SysFile, float, bool]:
        """上传表演背景音乐，超长自动截取前 4 分钟

        返回 (sys_file, 最终时长秒, 是否截取)
        """
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(msg="仅支持 mp3/wav 格式的音频文件")
        if not file_data:
            raise ValidationError(msg="音频文件内容为空")
        if len(file_data) > MAX_FILE_SIZE:
            raise ValidationError(msg="音频文件不能超过 20MB")

        duration, final_data, truncated = await asyncio.to_thread(_probe_and_truncate, file_data, ext)

        stored_name = generate_stored_name(ext)
        path_prefix = timezone.now().strftime("%Y/%m/%d")
        storage = get_storage_backend()
        file_path = await storage.save(final_data, stored_name, path_prefix)

        sys_file = SysFile(
            original_name=original_name,
            stored_name=stored_name,
            file_path=file_path,
            file_size=len(final_data),
            mime_type=mime_type,
            extension=ext,
            storage_platform=settings.STORAGE.PLATFORM,
            created_by=user_id,
        )
        db.add(sys_file)
        await db.flush()
        await db.refresh(sys_file)

        logger.info("表演背景音乐上传成功: %s -> %s (truncated=%s)", original_name, file_path, truncated)
        return sys_file, min(duration, float(MAX_DURATION_SECONDS)), truncated

    @staticmethod
    async def list_user_music(db: AsyncSession, user_id: int) -> list[SysFile]:
        """当前用户上传的表演背景音乐列表（仅自己可见）

        已被预设音乐映射（PRESET_MUSIC_FILE_IDS）占用的文件不再重复出现在上传列表中。
        """
        conditions = [
            SysFile.deleted_at.is_(None),
            SysFile.created_by == user_id,
            SysFile.extension.in_(ALLOWED_EXTENSIONS),
        ]
        preset_file_ids = set(PRESET_MUSIC_FILE_IDS.values())
        if preset_file_ids:
            conditions.append(SysFile.id.notin_(preset_file_ids))
        result = await db.execute(
            select(SysFile)
            .where(*conditions)
            .order_by(SysFile.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_user_music_with_duration(db: AsyncSession, user_id: int) -> list[tuple[SysFile, float | None]]:
        """当前用户上传的音乐列表，并探测每条音频的实际时长（秒）

        时长未持久化，列表时实时探测（并发执行）；探测失败的项时长返回 None，
        不影响列表整体返回。
        """
        files = await PerformanceMusicService.list_user_music(db, user_id)
        if not files:
            return []
        storage = get_storage_backend()

        async def _probe(item: SysFile) -> tuple[SysFile, float | None]:
            try:
                data = await storage.read(item.file_path)
                duration = await asyncio.to_thread(_probe_duration_bytes, data, item.extension)
                return item, duration
            except Exception as e:
                logger.warning("探测上传音乐时长失败: %s, %s", item.file_path, e)
                return item, None

        return list(await asyncio.gather(*(_probe(item) for item in files)))

    @staticmethod
    async def probe_durations_by_ids(db: AsyncSession, file_ids: set[int]) -> dict[int, float | None]:
        """按 sys_file_id 批量探测音频时长（并发），用于预设音乐试听映射的真实时长展示"""
        if not file_ids:
            return {}
        result = await db.execute(
            select(SysFile).where(SysFile.id.in_(file_ids), SysFile.deleted_at.is_(None))
        )
        files = list(result.scalars().all())
        storage = get_storage_backend()

        async def _probe(item: SysFile) -> tuple[int, float | None]:
            try:
                data = await storage.read(item.file_path)
                duration = await asyncio.to_thread(_probe_duration_bytes, data, item.extension)
                return item.id, duration
            except Exception as e:
                logger.warning("探测预设音乐时长失败: %s, %s", item.file_path, e)
                return item.id, None

        pairs = await asyncio.gather(*(_probe(item) for item in files))
        return dict(pairs)

    @staticmethod
    async def delete_music(db: AsyncSession, file_id: int, user_id: int) -> None:
        """删除自己上传的表演背景音乐；被表演任务引用的不允许删除（软删除）"""
        sys_file = await db.get(SysFile, file_id)
        if not sys_file or sys_file.deleted_at is not None or sys_file.extension not in ALLOWED_EXTENSIONS:
            raise NotFoundError(msg="音乐不存在或已删除")
        if sys_file.created_by != user_id:
            raise ForbiddenError(msg="只能删除自己上传的音乐")

        token = f"{UPLOAD_MUSIC_PREFIX}{file_id}"
        ref = await db.execute(
            select(Task.id)
            .where(
                Task.deleted_at.is_(None),
                cast(Task.performance_steps, String).like(f"%{token}%"),
            )
            .limit(1)
        )
        if ref.first() is not None:
            raise ConflictError(msg="该音乐已被表演任务引用，无法删除")

        sys_file.deleted_at = timezone.now()
        logger.info("表演背景音乐删除成功: file_id=%d, %s", file_id, sys_file.original_name)

    @staticmethod
    async def validate_music_refs(db: AsyncSession, music_values: list[str]) -> None:
        """校验表演步骤中 upload:<file_id> 引用的音频文件存在且未删除"""
        file_ids = {fid for v in music_values if (fid := parse_upload_file_id(v)) is not None}
        if not file_ids:
            return
        result = await db.execute(
            select(SysFile.id).where(
                SysFile.id.in_(file_ids),
                SysFile.deleted_at.is_(None),
                SysFile.extension.in_(ALLOWED_EXTENSIONS),
            )
        )
        existing = {row[0] for row in result.all()}
        missing = file_ids - existing
        if missing:
            raise ValidationError(msg=f"背景音乐不存在或已被删除: {sorted(missing)}")
