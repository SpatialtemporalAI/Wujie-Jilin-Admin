"""
Path bridge: app.grpc.generated.config -> backend/grpc/generated/config

`*_pb2_grpc.py` 硬编码了 `import app.grpc.generated.config.voice_pb2` 等，
通过把本包的 __path__ 指向 git 子模块 `backend/grpc/generated/config/`，
让该导入解析到 submodule 实际生成文件，无需复制副本。
"""
import os

# __file__: backend/app/grpc/generated/config/__init__.py
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
__path__ = [os.path.join(_backend_root, "grpc", "generated", "config")]
