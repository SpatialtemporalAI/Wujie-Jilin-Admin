import logging

import bcrypt

logger = logging.getLogger(__name__)


class PasswordHasher:
    """基于 bcrypt 的密码哈希工具。"""

    @staticmethod
    def hash(password: str) -> str:
        """
        对密码进行 bcrypt 哈希。
        Returns:
            bcrypt_hash — salt 内嵌于 bcrypt 哈希中。
        """
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
        return hashed.decode("utf-8")

    @staticmethod
    def verify(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            # 非法/非 bcrypt 哈希（如明文、其它算法、被截断）——按验证失败处理，
            # 避免向上抛出 ValueError 被全局处理器转成不透明的 400。
            logger.warning("密码哈希格式非法，按验证失败处理")
            return False
