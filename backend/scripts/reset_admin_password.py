"""
重置 admin 用户密码为 bcrypt 哈希（"123456"）。
一次性脚本，运行后可删除。
"""

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.sys.user import SysUser
from core.security.password import PasswordHasher


def reset_admin_password():
    sync_url = "postgresql+psycopg2://postgres:123456@localhost:5432/smilex_cloud"
    engine = create_engine(sync_url, echo=False)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        try:
            stmt = select(SysUser).where(SysUser.username == "admin")
            result = session.execute(stmt)
            admin = result.scalar_one_or_none()

            if not admin:
                print("未找到 admin 用户，跳过")
                return

            new_password = "admin123"
            hashed = PasswordHasher.hash(new_password)
            admin.password = hashed
            session.commit()

            print(f"admin 密码已重置为: {new_password}")
            print(f"密码哈希: {hashed}")
        except Exception as e:
            print(f"重置密码失败: {str(e)}")
            session.rollback()
        finally:
            engine.dispose()


if __name__ == "__main__":
    reset_admin_password()
