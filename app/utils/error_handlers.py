"""
错误处理工具
统一处理API错误和异常
"""
import functools
from typing import Callable, Any
from fastapi import HTTPException
from app.services.logging_service import logging_service
from app.services.response_service import response_service


def handle_api_errors(func: Callable) -> Callable:
    """API错误处理装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 记录错误日志
            logging_service.log_error_with_context(
                f"API错误: {func.__name__}",
                e,
                args=str(args)[:100],
                kwargs=str(kwargs)[:100]
            )
            # 返回通用错误响应
            raise response_service.internal_error(f"处理请求时发生错误: {str(e)}")
    
    return wrapper


def handle_sync_errors(func: Callable) -> Callable:
    """同步函数错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 记录错误日志
            logging_service.log_error_with_context(
                f"同步函数错误: {func.__name__}",
                e,
                args=str(args)[:100],
                kwargs=str(kwargs)[:100]
            )
            # 返回None或默认值
            return None
    
    return wrapper


def validate_required_params(params: dict, required_fields: list) -> None:
    """验证必需参数"""
    missing_fields = [field for field in required_fields if field not in params or params[field] is None]
    if missing_fields:
        raise response_service.bad_request(f"缺少必需参数: {', '.join(missing_fields)}")


def validate_file_upload(file, max_size: int = None, allowed_types: list = None) -> None:
    """验证文件上传"""
    if not file:
        raise response_service.bad_request("未提供文件")
    
    if max_size and hasattr(file, 'size') and file.size > max_size:
        raise response_service.bad_request(f"文件大小超过限制: {max_size} bytes")
    
    if allowed_types and hasattr(file, 'content_type'):
        if file.content_type not in allowed_types:
            raise response_service.bad_request(f"不支持的文件类型: {file.content_type}")


def safe_json_serialize(data: Any) -> Any:
    """安全的JSON序列化"""
    try:
        import json
        json.dumps(data)
        return data
    except (TypeError, ValueError):
        # 如果无法序列化，返回字符串表示
        return str(data)
