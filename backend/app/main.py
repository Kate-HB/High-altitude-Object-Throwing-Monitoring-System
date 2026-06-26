import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.health import router as health_router
from backend.app.api.system import router as system_router
from backend.app.api.videos import router as videos_router
from backend.app.core.config import get_settings
from backend.app.core.database import init_db

# Runtime directories created on startup
RUNTIME_DIRS = ["uploads", "outputs", "events/snapshots", "logs"]


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_dir / "backend.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    for d in RUNTIME_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)
    logging.getLogger("backend").info("Runtime directories ready: %s", RUNTIME_DIRS)
    init_db()
    logging.getLogger("backend").info("Database initialized")
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(videos_router, prefix="/api")
