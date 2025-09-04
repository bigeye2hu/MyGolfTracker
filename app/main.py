from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes.health import router as health_router
from .routes.analyze import router as analyze_router
from .routes.convert import router as convert_router


def create_app() -> FastAPI:
    app = FastAPI(title="GolfTracker Service", version="0.1.0")
    
    # 添加 CORS 中间件支持本地测试
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health_router)
    app.include_router(analyze_router, prefix="/analyze")
    app.include_router(convert_router, prefix="/convert")
    
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    return app


app = create_app()


