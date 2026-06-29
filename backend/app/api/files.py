"""Static file serving for result videos and snapshots."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(tags=["files"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/files")
def serve_file(path: str = Query(..., description="Relative path from project root")):
    """Serve a file from the project directory (result videos, snapshots)."""
    full = _PROJECT_ROOT / path
    resolved = full.resolve()
    if not str(resolved).startswith(str(_PROJECT_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="路径越界")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(resolved))
