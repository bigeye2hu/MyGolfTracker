"""
文件服务
统一管理文件操作和视频处理
"""
import os
import tempfile
import shutil
import cv2
from typing import Dict, Any, List, Tuple
from app.config import VIDEO_ANALYSIS_CONFIG


class FileService:
    """文件服务 - 统一管理文件操作"""
    
    def __init__(self):
        self.config = VIDEO_ANALYSIS_CONFIG
    
    def create_temp_file(self, suffix: str = ".mp4") -> str:
        """创建临时文件"""
        return tempfile.mktemp(suffix=suffix)
    
    def save_uploaded_file(self, file: Any, suffix: str = None) -> str:
        """保存上传的文件到临时位置"""
        if suffix is None:
            suffix = os.path.splitext(getattr(file, 'filename', 'video.mp4'))[1]
        
        temp_path = self.create_temp_file(suffix)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return temp_path
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except Exception as e:
            print(f"清理临时文件失败: {e}")
        return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"error": "无法打开视频文件"}
            
            info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": int(cap.get(cv2.CAP_PROP_FPS)),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration": 0
            }
            
            if info["fps"] > 0:
                info["duration"] = info["frame_count"] / info["fps"]
            
            cap.release()
            return info
            
        except Exception as e:
            return {"error": f"获取视频信息失败: {str(e)}"}
    
    def extract_frame(self, video_path: str, frame_number: int) -> bytes:
        """提取指定帧的图片数据"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config["jpeg_quality"]])
                return buffer.tobytes()
            else:
                return b""
        except Exception as e:
            print(f"提取帧失败: {e}")
            return b""
    
    def extract_frames(self, video_path: str, frame_numbers: List[int]) -> List[Dict[str, Any]]:
        """批量提取帧数据"""
        frames_data = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            for i, frame_num in enumerate(frame_numbers):
                if frame_num >= total_frames:
                    continue
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config["jpeg_quality"]])
                    frame_data = {
                        "frame_number": frame_num,
                        "timestamp": frame_num / fps if fps > 0 else 0,
                        "image_data": buffer.tobytes(),
                        "filename": f"frame_{frame_num:06d}.jpg"
                    }
                    frames_data.append(frame_data)
            
            cap.release()
            return frames_data
            
        except Exception as e:
            print(f"批量提取帧失败: {e}")
            return []
    
    def is_supported_format(self, filename: str) -> bool:
        """检查文件格式是否支持"""
        if not filename:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.config["supported_formats"]
    
    def get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0


# 全局文件服务实例
file_service = FileService()
