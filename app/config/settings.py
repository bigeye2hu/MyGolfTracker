"""
应用配置管理
统一管理所有常量和配置项
"""
import os
from typing import Dict, Any

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5005,
    "max_concurrent_conversions": 3,
    "default_server_load": "normal"
}

# 视频分析配置
VIDEO_ANALYSIS_CONFIG = {
    "default_resolution": "480",
    "default_confidence": "0.01",
    "default_iou": "0.7",
    "default_max_det": "10",
    "default_optimization_strategy": "auto_fill",
    "supported_formats": ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "jpeg_quality": 90
}

# 轨迹优化配置
TRAJECTORY_CONFIG = {
    "default_strategies": [
        "real_savitzky_golay",
        "real_linear_interpolation", 
        "real_outlier_detection",
        "real_physics_constraints",
        "real_trajectory_optimization",
        "conservative_interpolation",
        "outlier_only",
        "minimal_processing",
        "smart_interpolation"
    ]
}

# 挥杆状态配置
SWING_STATE_CONFIG = {
    "phases": [
        "Address",
        "Backswing", 
        "Transition",
        "Downswing",
        "Impact",
        "FollowThrough",
        "Finish"
    ]
}

# 文件路径配置
FILE_PATHS = {
    "static_dir": "static",
    "temp_dir": "/tmp",
    "model_dir": "data"
}

# 数据库配置（如果需要）
DATABASE_CONFIG = {
    "type": "memory",  # 当前使用内存存储
    "job_store": {},
    "analysis_results": {},
    "conversion_jobs": {}
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# 获取环境变量配置
def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    return {
        "server": SERVER_CONFIG,
        "video_analysis": VIDEO_ANALYSIS_CONFIG,
        "trajectory": TRAJECTORY_CONFIG,
        "swing_state": SWING_STATE_CONFIG,
        "file_paths": FILE_PATHS,
        "database": DATABASE_CONFIG,
        "logging": LOGGING_CONFIG
    }

# 环境特定配置
def get_env_config() -> Dict[str, Any]:
    """获取环境特定配置"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "debug": False,
            "reload": False,
            "log_level": "WARNING"
        }
    else:
        return {
            "debug": True,
            "reload": True,
            "log_level": "INFO"
        }
