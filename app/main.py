from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import torch
import time
import os
from .routes.health import router as health_router
from .routes.analyze import router as analyze_router
from .routes.convert import router as convert_router
from .routes.monitoring import router as monitoring_router
from .routes.welcome import router as welcome_router
from .utils.metrics_store import add_request_metric
from analyzer.config import MODEL_PATH

# 全局模型变量
MODEL = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，包含模型预热"""
    global MODEL
    
    # 启动时加载模型
    print("🚀 正在启动 GolfTracker 服务...")
    try:
        # 检查 CUDA 可用性
        cuda_available = torch.cuda.is_available()
        print(f"🔧 CUDA 可用性: {cuda_available}")
        
        if cuda_available:
            print(f"🎯 GPU 设备: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU 内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # 加载模型（延迟加载，这里只做预热）
        print("📦 正在预热模型...")
        from ultralytics import YOLO
        MODEL = YOLO(MODEL_PATH)
        
        # 模型预热：运行一次假的推理确保GPU上下文就绪
        if cuda_available:
            MODEL.to("cuda")
            if hasattr(MODEL, "model") and hasattr(MODEL.model, "half"):
                MODEL.model.half = True
        else:
            MODEL.to("cpu")
            if hasattr(MODEL, "model") and hasattr(MODEL.model, "half"):
                MODEL.model.half = False
        
        # 运行预热推理
        import numpy as np
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        MODEL.predict(
            source=dummy_image,
            verbose=False,
            device="cuda" if cuda_available else "cpu",
            imgsz=480,
            conf=0.01,
            iou=0.7,
            max_det=10,
            agnostic_nms=False,
            augment=False,
        )
        
        print("✅ 模型预热完成，服务已就绪")
        
    except Exception as e:
        print(f"⚠️ 模型加载失败: {e}")
        MODEL = None
    
    yield
    
    # 关闭时清理资源
    print("🛑 正在关闭 GolfTracker 服务...")
    if MODEL is not None:
        del MODEL
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("✅ 服务已关闭")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GolfTracker Service", 
        version="0.1.0",
        lifespan=lifespan
    )
    
    # 添加 CORS 中间件支持本地测试
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加请求跟踪中间件
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        """中间件：跟踪请求统计"""
        start_time = time.time()
        
        response = await call_next(request)
        
        # 记录请求信息
        process_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        request_info = {
            "timestamp": time.time(),
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "response_time": round(process_time, 2)
        }
        
        add_request_metric(request_info)
        
        return response
    
    
    # 添加健康检查端点
    @app.get("/healthz")
    def healthz():
        """Kubernetes 健康检查端点"""
        cuda_available = torch.cuda.is_available()
        model_loaded = MODEL is not None
        
        status = "ok" if model_loaded else "degraded"
        
        return {
            "status": status,
            "cuda": cuda_available,
            "model_loaded": model_loaded,
            "timestamp": time.time()
        }
    
    # 添加 Prometheus 监控端点
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        instrumentator = Instrumentator()
        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics")
        print("📊 Prometheus 监控已启用")
    except ImportError:
        print("⚠️ prometheus_fastapi_instrumentator 未安装，跳过监控端点")
    except Exception as e:
        print(f"⚠️ Prometheus 监控设置失败: {e}")
    
    app.include_router(welcome_router)
    app.include_router(health_router)
    app.include_router(analyze_router, prefix="/analyze")
    app.include_router(convert_router, prefix="/convert")
    app.include_router(monitoring_router)
    
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    return app


app = create_app()


