"""
视频分析服务 - 从analyze.py中提取的视频分析逻辑
保持原有的分析逻辑和界面完全不变
"""
from typing import Dict, Any
import os
import tempfile
import shutil
import threading
import uuid
import time
import json
import base64
from datetime import datetime
import zipfile
import io

import numpy as np
import cv2

from detector.yolov8_detector import YOLOv8Detector
from detector.pose_detector import PoseDetector
from analyzer.ffmpeg import iter_video_frames
from analyzer.swing_analyzer import SwingAnalyzer
from analyzer.trajectory_optimizer import TrajectoryOptimizer
from analyzer.swing_state_machine import SwingStateMachine, SwingPhase
from analyzer.strategy_manager import get_strategy_manager
from app.utils.helpers import get_mp_landmark_names, calculate_trajectory_distance, clean_json_data, check_video_compatibility
from app.config import VIDEO_ANALYSIS_CONFIG


class VideoAnalysisService:
    """视频分析服务 - 保持原有逻辑和界面"""
    
    def __init__(self):
        self.job_store: Dict[str, Dict] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        self.config = VIDEO_ANALYSIS_CONFIG
    
    def analyze_video_job(self, job_id: str, video_path: str, resolution: str = None, confidence: str = None, iou: str = None, max_det: str = None, optimization_strategy: str = None) -> None:
        """分析视频任务 - 保持原有逻辑"""
        # 使用配置中的默认值
        resolution = resolution or self.config["default_resolution"]
        confidence = confidence or self.config["default_confidence"]
        iou = iou or self.config["default_iou"]
        max_det = max_det or self.config["default_max_det"]
        optimization_strategy = optimization_strategy or self.config["default_optimization_strategy"]
        
        # 暂时调用原来的函数，稍后会完全替换
        from app.routes.analyze import _analyze_video_job
        return _analyze_video_job(job_id, video_path, resolution, confidence, iou, max_det, optimization_strategy)
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取任务状态 - 保持原有逻辑"""
        # 暂时调用原来的逻辑，稍后会完全替换
        from app.routes.analyze import _JOB_STORE
        job = _JOB_STORE.get(job_id)
        if not job:
            return {"error": "任务不存在"}
        return job
    
    def get_analysis_result(self, job_id: str) -> Dict[str, Any]:
        """获取分析结果 - 保持原有逻辑"""
        # 暂时调用原来的逻辑，稍后会完全替换
        from app.routes.analyze import _ANALYSIS_RESULTS
        return _ANALYSIS_RESULTS.get(job_id, {})


# 全局服务实例
video_analysis_service = VideoAnalysisService()