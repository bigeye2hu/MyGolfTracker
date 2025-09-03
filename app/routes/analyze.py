from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
import os
import tempfile
import shutil
from typing import List, Dict, Tuple
import threading
import uuid
import time
import json

import numpy as np
import cv2

from detector.yolov8_detector import YOLOv8Detector
from detector.pose_detector import PoseDetector
from analyzer.ffmpeg import iter_video_frames
from analyzer.swing_analyzer import SwingAnalyzer
from analyzer.trajectory_optimizer import TrajectoryOptimizer


router = APIRouter()

# 简易后台任务存储
_JOB_STORE: Dict[str, Dict] = {}

def _analyze_video_job(job_id: str, video_path: str) -> None:
    try:
        _JOB_STORE[job_id]["status"] = "running"
        detector = YOLOv8Detector()
        trajectory = []
        frame_detections = []
        total_frames = 0
        detected_frames = 0
        total_confidence = 0.0

        cap = cv2.VideoCapture(video_path)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_fps = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()

        # 定义安全浮点数转换函数
        def safe_float(value):
            """确保浮点数值是JSON兼容的"""
            if value is None or (isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf'))):
                return 0.0
            return float(value)
        
        def clean_trajectory(trajectory):
            """清理轨迹中的NaN值"""
            cleaned = []
            for point in trajectory:
                if isinstance(point, list) and len(point) >= 2:
                    x = safe_float(point[0])
                    y = safe_float(point[1])
                    cleaned.append([x, y])
                else:
                    cleaned.append([0.0, 0.0])
            return cleaned
        
        # 处理每一帧，提高检测精度
        for ok, frame_bgr in iter_video_frames(video_path, sample_stride=1, max_size=960):
            if not ok:
                break
            res = detector.detect_single_point(frame_bgr)
            if res is not None:
                cx, cy, conf = res
                # 获取当前帧的实际尺寸（可能被缩放）
                frame_h, frame_w = frame_bgr.shape[:2]
                
                # 计算缩放比例
                scale_x = video_width / frame_w
                scale_y = video_height / frame_h
                
                # 将检测坐标映射回原始视频坐标
                orig_x = cx * scale_x
                orig_y = cy * scale_y
                
                # 确保坐标在有效范围内
                x = max(0, min(video_width, int(orig_x)))
                y = max(0, min(video_height, int(orig_y)))
                
                trajectory.append([x, y])
                frame_detections.append({
                    "frame": total_frames,
                    "x": int(safe_float(x)),
                    "y": int(safe_float(y)),
                    "norm_x": safe_float((x / video_width) if video_width else 0.0),
                    "norm_y": safe_float((y / video_height) if video_height else 0.0),
                    "confidence": safe_float(conf),
                    "detected": True
                })
                detected_frames += 1
                total_confidence += conf
            else:
                trajectory.append([0, 0])
                frame_detections.append({
                    "frame": total_frames,
                    "x": 0,
                    "y": 0,
                    "norm_x": 0.0,
                    "norm_y": 0.0,
                    "confidence": 0.0,
                    "detected": False
                })
            total_frames += 1
            # 简单进度，每处理100帧打点
            if total_frames % 100 == 0:
                _JOB_STORE[job_id]["progress"] = total_frames

        avg_confidence = total_confidence / detected_frames if detected_frames > 0 else 0.0
        detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0.0

        # 将像素坐标转换为归一化坐标，与API保持一致
        norm_trajectory = []
        for x, y in trajectory:
            if x == 0 and y == 0:  # 未检测到
                norm_trajectory.append([0.0, 0.0])
            else:
                norm_x = safe_float(x / video_width)
                norm_y = safe_float(y / video_height)
                norm_trajectory.append([norm_x, norm_y])
        
        # 清理轨迹数据
        norm_trajectory = clean_trajectory(norm_trajectory)

        # 为了对比，我们也生成优化后的轨迹（但不使用）
        from analyzer.trajectory_optimizer import TrajectoryOptimizer
        from analyzer.fast_motion_optimizer import FastMotionOptimizer
        
        # 使用标准优化器
        trajectory_optimizer = TrajectoryOptimizer()
        optimized_trajectory, _ = trajectory_optimizer.optimize_trajectory(norm_trajectory)
        optimized_trajectory = clean_trajectory(optimized_trajectory)
        
        # 使用快速移动优化器
        fast_motion_optimizer = FastMotionOptimizer(confidence_threshold=0.3, velocity_threshold=0.15)
        fast_motion_trajectory, _ = fast_motion_optimizer.optimize_trajectory(norm_trajectory)
        fast_motion_trajectory = clean_trajectory(fast_motion_trajectory)

        result = {
            "total_frames": total_frames,
            "detected_frames": detected_frames,
            "detection_rate": round(detection_rate, 2),
            "avg_confidence": round(avg_confidence, 3),
            "club_head_trajectory": norm_trajectory,  # 原始轨迹（归一化坐标）
            "optimized_trajectory": optimized_trajectory,  # 标准优化后的轨迹
            "fast_motion_trajectory": fast_motion_trajectory,  # 快速移动优化后的轨迹
            "frame_detections": frame_detections,
            "video_info": {
                "width": video_width,
                "height": video_height,
                "fps": video_fps
            }
        }
        _JOB_STORE[job_id]["status"] = "done"
        _JOB_STORE[job_id]["result"] = result
    except Exception as e:
        _JOB_STORE[job_id]["status"] = "error"
        _JOB_STORE[job_id]["error"] = str(e)
    finally:
        try:
            os.remove(video_path)
        except Exception:
            pass


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
        for ok, frame_bgr in iter_video_frames(tmp_path, sample_stride=1, max_size=960):
            if not ok:
                break
                
            # 杆头检测
            res = detector.detect_single_point(frame_bgr)
            if res is not None:
                cx, cy, conf = res
                # 获取当前帧的实际尺寸（可能被缩放）
                frame_h, frame_w = frame_bgr.shape[:2]
                
                # 计算缩放比例
                scale_x = video_spec["width"] / frame_w
                scale_y = video_spec["height"] / frame_h
                
                # 将检测坐标映射回原始视频坐标
                orig_x = cx * scale_x
                orig_y = cy * scale_y
                
                # 转换为归一化坐标 (0-1)
                norm_x = orig_x / video_spec["width"]
                norm_y = orig_y / video_spec["height"]
                
                # 确保坐标在有效范围内
                norm_x = max(0.0, min(1.0, norm_x))
                norm_y = max(0.0, min(1.0, norm_y))
                
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

        # 禁用轨迹优化，直接使用原始数据
        # optimized_trajectory, quality_scores = trajectory_optimizer.optimize_trajectory(trajectory)
        # trajectory_stats = trajectory_optimizer.get_trajectory_statistics(optimized_trajectory)
        
        # 使用原始轨迹数据
        optimized_trajectory = trajectory
        quality_scores = [1.0] * len(trajectory)  # 原始数据质量评分设为1.0
        trajectory_stats = {"valid_points": len(trajectory), "total_points": len(trajectory), "coverage": 1.0}

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


@router.get("/server-test")
async def get_server_test_page():
    """返回服务器端测试页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GolfTracker 服务器端测试</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏌️ GolfTracker 服务器端测试</h1>
            <p>上传高尔夫挥杆视频，测试YOLOv8检测和生成golftrainer兼容数据</p>
            <div style="margin-top:8px;padding:8px 12px;border:1px solid #ddd;border-radius:8px;background:#f8f9fa;display:inline-block;color:#333;">
              <strong style="color:#2c3e50;">运行模式</strong>：CPU 增强 / 抽帧步长 <code style="background:#e9ecef;color:#495057;padding:2px 4px;border-radius:3px;">1</code> / 长边≤<code style="background:#e9ecef;color:#495057;padding:2px 4px;border-radius:3px;">960</code> / 推理分辨率 <code style="background:#e9ecef;color:#495057;padding:2px 4px;border-radius:3px;">512</code>
            </div>
        </div>
        
        <div class="content">
            <!-- 上传视频板块 -->
            <div id="uploadSection"></div>
            
            <!-- 分析结果板块 -->
            <div id="resultsSection" style="display: none;"></div>
        </div>
    </div>

    <!-- 模块化组件 -->
    <script src="/static/js/upload-module.js?v=1.6"></script>
    <script src="/static/js/results-module.js?v=1.6"></script>
    <script src="/static/js/trajectory-module.js?v=1.6"></script>
    <script src="/static/js/video-player-module.js?v=1.6"></script>
    <script src="/static/js/json-output-module.js?v=1.6"></script>
    <script src="/static/js/frame-analysis-module.js?v=1.6"></script>
    <script src="/static/js/main.js?v=1.6"></script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.post("/video")
async def analyze_video_test(video: UploadFile = File(...)):
    """分析上传的视频文件，返回YOLOv8检测结果"""
    print(f"收到视频上传请求: {video.filename}, 类型: {video.content_type}, 大小: {video.size}")
    
    try:
        # 支持更多视频格式的 MIME 类型
        supported_types = {
            "video/mp4", "video/quicktime", "video/x-msvideo", "video/avi",
            "video/mov", "application/octet-stream", "video/x-quicktime"
        }
        
        print(f"检查文件类型: {video.content_type}")
        if video.content_type not in supported_types:
            # 如果 MIME 类型检测失败，尝试根据文件扩展名判断
            filename = video.filename or ""
            supported_extensions = [".mp4", ".mov", ".avi", ".quicktime"]
            print(f"尝试根据扩展名判断: {filename}")
            if not any(filename.lower().endswith(ext) for ext in supported_extensions):
                print(f"文件类型不支持: {video.content_type}")
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {video.content_type}")
            else:
                print(f"根据扩展名判断，文件类型支持: {filename}")
        else:
            print(f"文件类型直接支持: {video.content_type}")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename or "video.mp4")[1]) as tmp:
            shutil.copyfileobj(video.file, tmp)
            tmp_path = tmp.name

        # 后台任务：生成 job_id 并启动线程处理
        job_id = str(uuid.uuid4())
        _JOB_STORE[job_id] = {"status": "queued", "progress": 0, "filename": video.filename}
        t = threading.Thread(target=_analyze_video_job, args=(job_id, tmp_path), daemon=True)
        t.start()
        return {"job_id": job_id, "status": "queued"}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/video/status")
async def analyze_video_status(job_id: str):
    job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") == "done":
        return {"job_id": job_id, "status": "done", "result": job.get("result")}
    if job.get("status") == "error":
        return {"job_id": job_id, "status": "error", "error": job.get("error")}
    return {"job_id": job_id, "status": job.get("status"), "progress": job.get("progress", 0)}
