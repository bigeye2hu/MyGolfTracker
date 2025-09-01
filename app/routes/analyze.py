from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
import os
import tempfile
import shutil
from typing import List, Dict, Tuple
import json

import numpy as np
import cv2

from detector.yolov8_detector import YOLOv8Detector
from detector.pose_detector import PoseDetector
from analyzer.ffmpeg import iter_video_frames
from analyzer.swing_analyzer import SwingAnalyzer
from analyzer.trajectory_optimizer import TrajectoryOptimizer


router = APIRouter()


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    handed: str = Form("right"),
) -> dict:
    # 支持更多视频格式的 MIME 类型
    supported_types = {
        "video/mp4", "video/quicktime", "video/x-msvideo", "video/avi",
        "video/mov", "application/octet-stream", "video/x-quicktime"
    }
    
    if file.content_type not in supported_types:
        # 如果 MIME 类型检测失败，尝试根据文件扩展名判断
        filename = file.filename or ""
        supported_extensions = [".mp4", ".mov", ".avi", ".quicktime"]
        if not any(filename.lower().endswith(ext) for ext in supported_extensions):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "video.mp4")[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    detector = YOLOv8Detector()
    pose_detector = PoseDetector()
    trajectory_optimizer = TrajectoryOptimizer()
    trajectory: List[List[float]] = []
    poses: List[str] = []
    landmarks_list: List[List[float]] = []
    video_spec = {"width": 0, "height": 0, "fps": 30, "num_frames": 0}

    try:
        # 获取视频信息
        cap = cv2.VideoCapture(tmp_path)
        video_spec["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_spec["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_spec["fps"] = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()

        # 检测杆头轨迹和人体姿态
        frame_index = 0
        for ok, frame_bgr in iter_video_frames(tmp_path):
            if not ok:
                break
                
            # 杆头检测
            res = detector.detect_single_point(frame_bgr)
            if res is not None:
                cx, cy, conf = res
                # 转换为归一化坐标 (0-1)
                norm_x = cx / video_spec["width"]
                norm_y = cy / video_spec["height"]
                trajectory.append([norm_x, norm_y])
            else:
                trajectory.append([0.0, 0.0])  # 未检测到时使用 (0,0)
            
            # 姿态检测
            pose_landmarks = pose_detector.detect_pose(frame_bgr)
            if pose_landmarks:
                pose = pose_detector.classify_golf_pose(pose_landmarks, handed)
                poses.append(pose)
                # 获取扁平化的关键点数据
                landmarks = pose_detector.get_landmarks_flat(pose_landmarks)
                landmarks_list.append(landmarks)
            else:
                poses.append("Unknown")
                landmarks_list.append([])
                
            frame_index += 1
        
        video_spec["num_frames"] = frame_index

        # 优化轨迹数据
        optimized_trajectory, quality_scores = trajectory_optimizer.optimize_trajectory(trajectory)
        trajectory_stats = trajectory_optimizer.get_trajectory_statistics(optimized_trajectory)

        # 分析挥杆相位
        swing_analyzer = SwingAnalyzer(optimized_trajectory, video_spec, poses)
        phases = swing_analyzer.analyze_swing_phases()
        
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    # 构建 golftrainer 兼容的响应格式
    response = {
        "version": 1.0,
        "video_spec": {
            "height": video_spec["height"],
            "width": video_spec["width"],
            "num_frames": video_spec["num_frames"],
            "fps": video_spec["fps"],
            "scale": 100,
            "rotate": ""
        },
        "video_input": {
            "fname": file.filename or "video.mp4",
            "size": 0  # 实际大小未知
        },
        "num_frames": video_spec["num_frames"],
        "pose_result": {
            "poses": poses,
            "handed": "RightHanded" if handed.lower() == "right" else "LeftHanded"
        },
        "club_head_result": {
            "norm_points": optimized_trajectory,
            "algos": ["YOLOv8_Optimized"] * len(optimized_trajectory),
            "quality_scores": quality_scores,
            "trajectory_stats": trajectory_stats
        },
        "mp_result": {
            "landmarks": _get_mp_landmark_names(),
            "norm_points": landmarks_list
        },
        "swing_analysis": {
            "phases": phases,
            "key_frames": phases.get("key_frames", {}),
            "summary": phases.get("summary", {})
        }
    }

    # 添加 iOS 兼容的关键字段
    response["pose_result"]["poses_count"] = 1
    
    # 移除 phases 字典中的嵌套信息，避免重复
    clean_phases = {k: v for k, v in phases.items() if k not in ["key_frames", "summary"]}
    response["swing_analysis"]["phases"] = clean_phases
    
    return response


def _get_mp_landmark_names() -> List[str]:
    """获取 MediaPipe 关键点名称列表"""
    return [
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer", "left_ear", "right_ear",
        "mouth_left", "mouth_right", "left_shoulder", "right_shoulder",
        "left_elbow", "right_elbow", "left_wrist", "right_wrist",
        "left_pinky", "right_pinky", "left_index", "right_index",
        "left_thumb", "right_thumb", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle",
        "left_heel", "right_heel", "left_foot_index", "right_foot_index"
    ]
