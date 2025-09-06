"""
配置模块
"""
from .settings import get_config, get_env_config, SERVER_CONFIG, VIDEO_ANALYSIS_CONFIG, LOGGING_CONFIG

__all__ = ['get_config', 'get_env_config', 'SERVER_CONFIG', 'VIDEO_ANALYSIS_CONFIG', 'LOGGING_CONFIG']
