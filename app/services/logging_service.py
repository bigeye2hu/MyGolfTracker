"""
日志服务
统一管理日志记录和错误处理
"""
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from app.config import LOGGING_CONFIG


class LoggingService:
    """日志服务 - 统一管理日志记录"""
    
    def __init__(self):
        self.config = LOGGING_CONFIG
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=getattr(logging, self.config["level"]),
            format=self.config["format"],
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('golftracker.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger('GolfTracker')
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(f"{message} {self._format_kwargs(kwargs)}")
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(f"{message} {self._format_kwargs(kwargs)}")
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """记录错误日志"""
        error_msg = f"{message} {self._format_kwargs(kwargs)}"
        if exception:
            error_msg += f"\n异常详情: {str(exception)}\n{traceback.format_exc()}"
        self.logger.error(error_msg)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(f"{message} {self._format_kwargs(kwargs)}")
    
    def _format_kwargs(self, kwargs: Dict[str, Any]) -> str:
        """格式化关键字参数"""
        if not kwargs:
            return ""
        return " ".join([f"{k}={v}" for k, v in kwargs.items()])
    
    def log_api_request(self, method: str, path: str, status_code: int, duration: float = None):
        """记录API请求日志"""
        message = f"API请求: {method} {path} -> {status_code}"
        if duration:
            message += f" (耗时: {duration:.3f}s)"
        self.info(message)
    
    def log_video_analysis(self, job_id: str, video_path: str, status: str, **kwargs):
        """记录视频分析日志"""
        self.info(f"视频分析: {job_id} | {video_path} | {status}", **kwargs)
    
    def log_error_with_context(self, context: str, error: Exception, **kwargs):
        """记录带上下文的错误"""
        self.error(f"错误上下文: {context}", exception=error, **kwargs)


# 全局日志服务实例
logging_service = LoggingService()
