from datetime import datetime
from datetime import timezone as datetime_timezone
import zoneinfo
from zoneinfo._common import ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"


class TimeZone:
    def __init__(
        self,
        timezone_str: str = DEFAULT_TIMEZONE,
        format_str: str = DEFAULT_FORMAT,
    ) -> None:
        self.format_str = format_str
        try:
            self.tz_info = zoneinfo.ZoneInfo(timezone_str)
        except ZoneInfoNotFoundError:
            import pytz

            self.tz_info = pytz.timezone(timezone_str)

    def now(self) -> datetime:
        """获取当前时区时间"""
        return datetime.now(self.tz_info)

    def from_datetime(self, t: datetime) -> datetime:
        """
        将 datetime 对象转换为当前时区时间
        :param t: 需要转换的 datetime 对象
        :return:
        """
        return t.astimezone(self.tz_info)

    def from_str(self, t_str: str, format_str: str | None = None) -> datetime:
        """
        将时间字符串转换为当前时区的 datetime 对象
        :param t_str: 时间字符串
        :param format_str: 时间格式字符串，默认为实例配置格式
        :return:
        """
        fmt = format_str or self.format_str
        return datetime.strptime(t_str, fmt).replace(tzinfo=self.tz_info)

    @staticmethod
    def to_str(t: datetime, format_str: str = DEFAULT_FORMAT) -> str:
        """
        将 datetime 对象转换为指定格式的时间字符串
        :param t: datetime 对象
        :param format_str: 时间格式字符串
        :return:
        """
        return t.strftime(format_str)

    @staticmethod
    def to_utc(t: datetime | int) -> datetime:
        """
        将 datetime 对象或时间戳转换为 UTC 时区时间
        :param t: 需要转换的 datetime 对象或时间戳
        :return:
        """
        if isinstance(t, datetime):
            return t.astimezone(datetime_timezone.utc)
        return datetime.fromtimestamp(t, tz=datetime_timezone.utc)


timezone = TimeZone()


def configure(timezone_str: str = DEFAULT_TIMEZONE, format_str: str = DEFAULT_FORMAT):
    """重置模块级 timezone 单例"""
    global timezone
    timezone = TimeZone(timezone_str=timezone_str, format_str=format_str)
