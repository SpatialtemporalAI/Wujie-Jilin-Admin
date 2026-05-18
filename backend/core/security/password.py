import bcrypt


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
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )
