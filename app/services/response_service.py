"""
响应服务
统一管理API响应格式和错误处理
"""
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import json
from datetime import datetime


class ResponseService:
    """响应服务 - 统一管理API响应"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", status_code: int = 200) -> Dict[str, Any]:
        """成功响应"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error(message: str, status_code: int = 400, details: Any = None) -> HTTPException:
        """错误响应"""
        error_data = {
            "success": False,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            error_data["details"] = details
        
        return HTTPException(status_code=status_code, detail=error_data)
    
    @staticmethod
    def not_found(message: str = "资源未找到") -> HTTPException:
        """404错误响应"""
        return ResponseService.error(message, 404)
    
    @staticmethod
    def bad_request(message: str = "请求参数错误") -> HTTPException:
        """400错误响应"""
        return ResponseService.error(message, 400)
    
    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> HTTPException:
        """500错误响应"""
        return ResponseService.error(message, 500)
    
    @staticmethod
    def html_response(content: str, status_code: int = 200) -> HTMLResponse:
        """HTML响应"""
        return HTMLResponse(content=content, status_code=status_code)
    
    @staticmethod
    def streaming_response(content: bytes, media_type: str, filename: str = None) -> StreamingResponse:
        """流式响应"""
        headers = {}
        if filename:
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers=headers
        )
    
    @staticmethod
    def job_response(job_id: str, status: str, progress: int = 0, result: Any = None, error: str = None) -> Dict[str, Any]:
        """任务响应"""
        response = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
        if result:
            response["result"] = result
        if error:
            response["error"] = error
        
        return response
    
    @staticmethod
    def validation_error(field: str, message: str) -> HTTPException:
        """验证错误响应"""
        return ResponseService.error(
            f"参数验证失败: {field}",
            details={"field": field, "message": message}
        )


# 全局响应服务实例
response_service = ResponseService()
