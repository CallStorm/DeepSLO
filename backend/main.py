import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routers import auth as auth_router
from .routers import users as users_router
from .routers import projects as projects_router
from .routers import ai_models as ai_models_router
from .routers import config as config_router
from .routers import probe as probe_router
from .routers import report_sync as report_sync_router
from .routers import slo_settings as slo_settings_router
from .routers import slo_screen as slo_screen_router
from .routers import slo_analysis as slo_analysis_router
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
app.include_router(slo_analysis_router.router, prefix="/slo/analysis", tags=["slo-analysis"]) 


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# 静态文件服务（用于提供前端构建产物）
# 注意：这个路由必须放在所有 API 路由之后
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # 提供前端 SPA 的 index.html（支持 Vue Router history 模式）
    # 这个通配路由会捕获所有未匹配的路径，用于前端路由
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 检查请求的文件是否存在
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # 否则返回 index.html（用于 Vue Router）
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        
        return {"error": "Not found"}


