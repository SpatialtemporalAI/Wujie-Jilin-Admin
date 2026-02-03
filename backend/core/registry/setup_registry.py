from core.exception import setup_exception_handlers, setup_exception_global_handlers
from database.plugins import setup_soft_delete_plug
from fastapi import FastAPI
from core.log import setup_logging


def setup_app(app: FastAPI):
    """
    注册全局信息
    """

    # 注册全局异常
    setup_exception_handlers(app)
    setup_exception_global_handlers(app)
    # 注册软删除插件
    setup_soft_delete_plug()

    # 注册日志
    setup_logging()
