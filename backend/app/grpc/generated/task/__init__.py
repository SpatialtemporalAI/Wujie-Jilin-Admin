"""
Path bridge: app.grpc.generated.task -> backend/grpc/generated/task

`task_pb2_grpc.py` 硬编码了 `import app.grpc.generated.task.task_pb2`，
通过把本包的 __path__ 指向 git 子模块 `backend/grpc/generated/task/`，
让该导入解析到 submodule 实际生成文件，无需复制副本。
"""
import os

# __file__: backend/app/grpc/generated/task/__init__.py
# 上溯 5 层 -> backend
_backend_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        )
    )
)
__path__ = [os.path.join(_backend_root, "grpc", "generated", "task")]
