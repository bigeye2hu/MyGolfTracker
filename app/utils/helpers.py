"""
辅助函数模块 - 从analyze.py中提取的辅助函数
"""
import os
from typing import List, Dict, Any


def get_mp_landmark_names() -> List[str]:
    """获取MediaPipe关键点名称列表"""
    return [
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer",
        "left_ear", "right_ear", "mouth_left", "mouth_right",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_pinky", "right_pinky",
        "left_index", "right_index", "left_thumb", "right_thumb",
        "left_hip", "right_hip", "left_knee", "right_knee",
        "left_ankle", "right_ankle", "left_heel", "right_heel",
        "left_foot_index", "right_foot_index"
    ]


def calculate_trajectory_distance(trajectory: List[List[float]]) -> float:
    """计算轨迹总距离"""
    if len(trajectory) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(1, len(trajectory)):
        prev_point = trajectory[i-1]
        curr_point = trajectory[i]
        
        # 计算欧几里得距离
        distance = ((curr_point[0] - prev_point[0])**2 + 
                   (curr_point[1] - prev_point[1])**2)**0.5
        total_distance += distance
    
    return total_distance


def clean_json_data(data):
    """递归清理JSON数据中的NaN和无穷大值"""
    if isinstance(data, dict):
        return {key: clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, float):
        if data != data:  # NaN检查
            return None
        elif data == float('inf') or data == float('-inf'):
            return None
        else:
            return data
    else:
        return data


def check_video_compatibility(video_path: str) -> dict:
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