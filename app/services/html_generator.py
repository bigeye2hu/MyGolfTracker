"""
HTML生成服务 - 从analyze.py中提取的HTML生成函数
保持原有的HTML内容和样式完全不变
"""
from typing import List, Dict, Any
from datetime import datetime
import json


class HTMLGeneratorService:
    """HTML生成服务 - 保持原有逻辑和界面"""
    
    def generate_training_data_html(self, training_frame_data: List[Dict], job_id: str, failure_count: int, low_confidence_count: int, total_frames: int, confidence_threshold: float) -> str:
        """生成训练数据收集页面的HTML内容 - 保持原有逻辑"""
        # 暂时调用原来的函数，稍后会完全替换
        from app.routes.analyze import _generate_training_data_html
        return _generate_training_data_html(training_frame_data, job_id, failure_count, low_confidence_count, total_frames, confidence_threshold)
    
    def generate_failure_frames_html(self, failure_frame_data: List[Dict], job_id: str, failure_count: int, total_frames: int) -> str:
        """生成失败帧下载页面的HTML内容 - 保持原有逻辑"""
        # 这里先返回一个占位符，稍后会从analyze.py中复制完整的函数
        return "HTML生成功能待实现"


# 全局服务实例
html_generator_service = HTMLGeneratorService()