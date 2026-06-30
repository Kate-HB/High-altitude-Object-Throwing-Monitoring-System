"""System status endpoint — requires auth."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.auth import verify_token
from backend.app.core.database import get_db
from backend.app.models.schemas import success_response

router = APIRouter(tags=["system"])


@router.get("/system/status")
def system_status(_auth: dict = Depends(verify_token)) -> dict:
    # Backend
    backend_info = {"status": "running", "message": "后端服务正常"}

    # Database
    try:
        db = get_db()
        db.execute("SELECT 1")
        db.close()
        database_info = {"status": "connected", "message": "SQLite连接正常"}
    except sqlite3.Error:
        database_info = {"status": "error", "message": "数据库连接异常"}

    # Algorithm
    model_path = Path("models/best.onnx")
    model_loaded = model_path.exists()
    algorithm_info = {
        "status": "ready" if model_loaded else "missing_model",
        "model_loaded": model_loaded,
        "message": "算法模块可用" if model_loaded else "模型文件不存在",
    }

    # Device
    try:
        import torch  # type: ignore

        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else ""
        device_type = "gpu" if cuda_available else "cpu"
    except ImportError:
        cuda_available = False
        gpu_name = ""
        device_type = "cpu"

    device_info = {
        "device_type": device_type,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "cpu_fallback": True,
    }

    return success_response(
        {
            "backend": backend_info,
            "database": database_info,
            "algorithm": algorithm_info,
            "device": device_info,
        }
    )
