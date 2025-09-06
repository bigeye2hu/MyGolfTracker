"""
视频处理服务
统一管理视频分析的核心逻辑
"""
import os
import tempfile
import shutil
import threading
import uuid
import time
from typing import Dict, Any, List, Tuple
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
from app.services.file_service import file_service
from app.services.task_manager import task_manager


class VideoProcessingService:
    """视频处理服务 - 统一管理视频分析逻辑"""
    
    def __init__(self):
        self.config = VIDEO_ANALYSIS_CONFIG
    
    def safe_float(self, value):
        """确保浮点数值是JSON兼容的"""
        if value is None or (isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf'))):
            return 0.0
        return float(value)
    
    def clean_trajectory(self, trajectory):
        """清理轨迹中的NaN值"""
        cleaned = []
        for point in trajectory:
            if isinstance(point, list) and len(point) >= 2:
                x = self.safe_float(point[0])
                y = self.safe_float(point[1])
                cleaned.append([x, y])
            else:
                cleaned.append([0.0, 0.0])
        return cleaned
    
    def analyze_video(self, job_id: str, video_path: str, resolution: str = None, 
                     confidence: str = None, iou: str = None, max_det: str = None, 
                     optimization_strategy: str = None) -> None:
        """分析视频 - 核心分析逻辑"""
        # 使用配置中的默认值
        resolution = resolution or self.config["default_resolution"]
        confidence = confidence or self.config["default_confidence"]
        iou = iou or self.config["default_iou"]
        max_det = max_det or self.config["default_max_det"]
        optimization_strategy = optimization_strategy or self.config["default_optimization_strategy"]
        
        try:
            # 更新任务状态
            task_manager.update_job_status(job_id, "running", progress=0)
            
            # 初始化检测器
            detector = YOLOv8Detector()
            trajectory = []
            frame_detections = []
            total_frames = 0
            detected_frames = 0
            total_confidence = 0.0

            # 获取视频信息
            video_info = file_service.get_video_info(video_path)
            if "error" in video_info:
                task_manager.set_job_error(job_id, video_info["error"])
                return

            video_width = video_info["width"]
            video_height = video_info["height"]
            video_fps = video_info["fps"]

            # 处理参数
            resolution_int = int(resolution) if resolution.isdigit() else 480
            confidence_float = float(confidence) if confidence else 0.01
            iou_float = float(iou) if iou else 0.7
            max_det_int = int(max_det) if max_det.isdigit() else 10
            
            print(f"使用分析参数: 分辨率={resolution_int}×{resolution_int}, 置信度={confidence_float}, IoU={iou_float}, 最大检测={max_det_int}")

            # 处理每一帧
            for frame_idx, frame in enumerate(iter_video_frames(video_path, resolution_int)):
                total_frames += 1
                
                # 更新进度
                if total_frames % 10 == 0:
                    progress = min(20, (total_frames / 100) * 20)  # 前20%用于检测
                    task_manager.update_job_status(job_id, "running", progress=int(progress))

                # 检测杆头
                detections = detector.detect(frame, conf=confidence_float, iou=iou_float, max_det=max_det_int)
                
                if detections and len(detections) > 0:
                    detected_frames += 1
                    best_detection = max(detections, key=lambda x: x.conf)
                    confidence_val = float(best_detection.conf)
                    total_confidence += confidence_val
                    
                    # 计算相对坐标
                    x_center = best_detection.xyxy[0] + (best_detection.xyxy[2] - best_detection.xyxy[0]) / 2
                    y_center = best_detection.xyxy[1] + (best_detection.xyxy[3] - best_detection.xyxy[1]) / 2
                    
                    relative_x = x_center / frame.shape[1]
                    relative_y = y_center / frame.shape[0]
                    
                    trajectory.append([relative_x, relative_y])
                    frame_detections.append({
                        "frame": frame_idx,
                        "confidence": confidence_val,
                        "bbox": best_detection.xyxy.tolist(),
                        "relative_pos": [relative_x, relative_y]
                    })
                else:
                    trajectory.append([0.0, 0.0])
                    frame_detections.append({
                        "frame": frame_idx,
                        "confidence": 0.0,
                        "bbox": [0, 0, 0, 0],
                        "relative_pos": [0.0, 0.0]
                    })

            # 清理轨迹
            trajectory = self.clean_trajectory(trajectory)
            
            # 更新进度
            task_manager.update_job_status(job_id, "running", progress=25)

            # 轨迹优化
            print(f"🎯 开始轨迹优化处理，用户选择策略: {optimization_strategy}")
            print(f"📊 原始轨迹数据: {len(trajectory)} 个点")
            
            # 这里可以添加轨迹优化逻辑
            optimized_trajectory = trajectory  # 暂时使用原始轨迹
            
            # 更新进度
            task_manager.update_job_status(job_id, "running", progress=50)

            # 挥杆状态分析
            print("🎯 开始挥杆状态分析...")
            # 这里可以添加挥杆状态分析逻辑
            
            # 更新进度
            task_manager.update_job_status(job_id, "running", progress=75)

            # 生成结果
            result = {
                "job_id": job_id,
                "video_info": {
                    "width": video_width,
                    "height": video_height,
                    "fps": video_fps,
                    "total_frames": total_frames
                },
                "detection_stats": {
                    "total_frames": total_frames,
                    "detected_frames": detected_frames,
                    "detection_rate": detected_frames / total_frames if total_frames > 0 else 0,
                    "average_confidence": total_confidence / detected_frames if detected_frames > 0 else 0
                },
                "trajectory": {
                    "original": trajectory,
                    "optimized": optimized_trajectory,
                    "total_distance": calculate_trajectory_distance(optimized_trajectory)
                },
                "frame_detections": frame_detections,
                "analysis_params": {
                    "resolution": resolution_int,
                    "confidence": confidence_float,
                    "iou": iou_float,
                    "max_det": max_det_int,
                    "optimization_strategy": optimization_strategy
                }
            }

            # 设置任务结果
            task_manager.set_job_result(job_id, result)
            print(f"✅ 视频分析完成: {job_id}")

        except Exception as e:
            print(f"❌ 视频分析失败: {e}")
            import traceback
            traceback.print_exc()
            task_manager.set_job_error(job_id, str(e))


# 全局视频处理服务实例
video_processing_service = VideoProcessingService()
