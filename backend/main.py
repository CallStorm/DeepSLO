from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth as auth_router
from .routers import users as users_router
from .routers import projects as projects_router
from .routers import ai_models as ai_models_router
from .routers import config as config_router
from .routers import probe as probe_router
from .routers import report_sync as report_sync_router
from .routers import slo_settings as slo_settings_router
from .routers import slo_screen as slo_screen_router
from .bootstrap import ensure_admin_user, create_db_and_tables
from .services.sync_runner import start_background_sync_loop
from .services.slo_scheduler import start_slo_scheduler

app = FastAPI(title="DeepSLO API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    ensure_admin_user()
    start_background_sync_loop(interval_seconds=30)
    start_slo_scheduler(interval_hours=1)  # 每小时计算一次SLO


app.include_router(auth_router.router, prefix="/auth", tags=["auth"]) 
app.include_router(users_router.router, prefix="/system/users", tags=["users"]) 
app.include_router(projects_router.router, prefix="/system/projects", tags=["projects"]) 
app.include_router(ai_models_router.router, prefix="/system/ai-models", tags=["ai-models"]) 
app.include_router(config_router.router, prefix="/system/config", tags=["config"]) 
app.include_router(probe_router.router, prefix="/probe", tags=["probe"]) 
app.include_router(report_sync_router.router, prefix="/probe", tags=["probe-sync"])
app.include_router(slo_settings_router.router, prefix="/slo/settings", tags=["slo-settings"])
app.include_router(slo_screen_router.router, prefix="/slo/screen", tags=["slo-screen"]) 


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


