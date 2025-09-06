"""
文件工具函数
"""
import os
import tempfile
import shutil
from typing import Dict, Any


def check_video_compatibility(video_path: str) -> Dict[str, Any]:
    """检查视频兼容性"""
    try:
        # 检查文件是否存在
        if not os.path.exists(video_path):
            return {
                "compatible": False,
                "error": "文件不存在",
                "suggestions": ["请检查文件路径是否正确"]
            }
        
        # 检查文件大小
        file_size = os.path.getsize(video_path)
        if file_size == 0:
            return {
                "compatible": False,
                "error": "文件为空",
                "suggestions": ["请检查文件是否完整"]
            }
        
        # 检查文件扩展名
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        file_ext = os.path.splitext(video_path)[1].lower()
        
        if file_ext not in valid_extensions:
            return {
                "compatible": False,
                "error": f"不支持的文件格式: {file_ext}",
                "suggestions": [
                    "支持的格式: " + ", ".join(valid_extensions),
                    "请使用支持的视频格式"
                ]
            }
        
        return {
            "compatible": True,
            "file_size": file_size,
            "file_extension": file_ext,
            "suggestions": []
        }
        
    except Exception as e:
        return {
            "compatible": False,
            "error": f"检查失败: {str(e)}",
            "suggestions": ["请检查文件是否损坏"]
        }


def create_temp_file(suffix: str = ".mp4") -> str:
    """创建临时文件"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"清理临时文件失败: {e}")


def ensure_directory_exists(directory: str) -> None:
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件信息"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "exists": True
        }
    except Exception as e:
        return {
            "size": 0,
            "modified": 0,
            "created": 0,
            "exists": False,
            "error": str(e)
        }
