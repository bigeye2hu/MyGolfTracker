"""
视频分析服务
"""
import os
import tempfile
import shutil
import threading
import uuid
import time
from typing import Dict, Any

import numpy as np
import cv2

from detector.yolov8_detector import YOLOv8Detector
from detector.pose_detector import PoseDetector
from analyzer.ffmpeg import iter_video_frames
from analyzer.swing_analyzer import SwingAnalyzer
from analyzer.trajectory_optimizer import TrajectoryOptimizer
from analyzer.swing_state_machine import SwingStateMachine, SwingPhase
from analyzer.strategy_manager import get_strategy_manager


class VideoAnalysisService:
    """视频分析服务"""
    
    def __init__(self):
        self.job_store: Dict[str, Dict] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
    
    def start_analysis_job(self, job_id: str, video_path: str, resolution: str = "480", 
                          confidence: str = "0.01", iou: str = "0.7", max_det: str = "10", 
                          optimization_strategy: str = "original") -> None:
        """启动视频分析任务"""
        self.job_store[job_id] = {
            "status": "queued",
            "video_path": video_path,
            "resolution": resolution,
            "confidence": confidence,
            "iou": iou,
            "max_det": max_det,
            "optimization_strategy": optimization_strategy,
            "created_at": time.time()
        }
        
        # 在后台线程中运行分析
        thread = threading.Thread(
            target=self._analyze_video_job,
            args=(job_id, video_path, resolution, confidence, iou, max_det, optimization_strategy)
        )
        thread.daemon = True
        thread.start()
    
    def _analyze_video_job(self, job_id: str, video_path: str, resolution: str = "480", 
                          confidence: str = "0.01", iou: str = "0.7", max_det: str = "10", 
                          optimization_strategy: str = "original") -> None:
        """执行视频分析任务"""
        try:
            self.job_store[job_id]["status"] = "running"
            detector = YOLOv8Detector()
            pose_detector = PoseDetector()
            
            # 设置检测参数
            detector.set_confidence(float(confidence))
            detector.set_iou_threshold(float(iou))
            detector.set_max_detections(int(max_det))
            
            # 获取策略管理器
            strategy_manager = get_strategy_manager()
            strategy = strategy_manager.get_strategy(optimization_strategy)
            
            # 初始化分析器
            swing_analyzer = SwingAnalyzer()
            trajectory_optimizer = TrajectoryOptimizer(strategy=strategy)
            swing_state_machine = SwingStateMachine()
            
            # 分析视频
            results = self._process_video(
                video_path, detector, pose_detector, swing_analyzer, 
                trajectory_optimizer, swing_state_machine, resolution
            )
            
            # 存储结果
            self.analysis_results[job_id] = results
            self.job_store[job_id]["status"] = "done"
            self.job_store[job_id]["result"] = results
            
        except Exception as e:
            self.job_store[job_id]["status"] = "error"
            self.job_store[job_id]["error"] = str(e)
            print(f"分析任务 {job_id} 失败: {e}")
    
    def _process_video(self, video_path: str, detector, pose_detector, swing_analyzer, 
                      trajectory_optimizer, swing_state_machine, resolution: str) -> Dict[str, Any]:
        """处理视频帧"""
        frames = []
        detections = []
        poses = []
        swing_phases = []
        
        # 处理视频帧
        for frame_data in iter_video_frames(video_path, resolution):
            frame = frame_data['frame']
            frame_number = frame_data['frame_number']
            timestamp = frame_data['timestamp']
            
            # 检测杆头
            detection = detector.detect(frame)
            detections.append(detection)
            
            # 检测姿态
            pose = pose_detector.detect(frame)
            poses.append(pose)
            
            # 分析挥杆阶段
            swing_phase = swing_state_machine.update(detection, pose)
            swing_phases.append(swing_phase)
            
            frames.append({
                'frame_number': frame_number,
                'timestamp': timestamp,
                'frame': frame
            })
        
        # 优化轨迹
        club_head_trajectory = trajectory_optimizer.optimize_trajectory(detections)
        
        # 分析挥杆
        swing_analysis = swing_analyzer.analyze_swing(club_head_trajectory, swing_phases)
        
        # 计算统计信息
        total_frames = len(frames)
        detected_frames = sum(1 for d in detections if d['confidence'] > 0)
        detection_rate = (detected_frames / total_frames) * 100 if total_frames > 0 else 0
        avg_confidence = np.mean([d['confidence'] for d in detections if d['confidence'] > 0]) if detected_frames > 0 else 0
        
        return {
            'total_frames': total_frames,
            'detected_frames': detected_frames,
            'detection_rate': round(detection_rate, 2),
            'avg_confidence': round(avg_confidence, 3),
            'club_head_trajectory': club_head_trajectory,
            'swing_phases': swing_phases,
            'swing_analysis': swing_analysis,
            'video_info': {
                'fps': 30,  # 可以从视频元数据获取
                'duration': frames[-1]['timestamp'] if frames else 0,
                'resolution': resolution
            }
        }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if job_id not in self.job_store:
            return {"status": "not_found"}
        
        job = self.job_store[job_id]
        if job["status"] == "done":
            return {
                "status": "done",
                "result": job.get("result", {}),
                "job_id": job_id
            }
        elif job["status"] == "error":
            return {
                "status": "error",
                "error": job.get("error", "未知错误"),
                "job_id": job_id
            }
        else:
            return {
                "status": job["status"],
                "job_id": job_id
            }
    
    def get_analysis_result(self, job_id: str) -> Dict[str, Any]:
        """获取分析结果"""
        return self.analysis_results.get(job_id, {})


# 全局服务实例
video_analysis_service = VideoAnalysisService()
