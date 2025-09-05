from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
import os
import tempfile
import shutil
from typing import List, Dict, Tuple, Any
import threading
import uuid
import time
import json
import base64
from datetime import datetime

import numpy as np
import cv2

from detector.yolov8_detector import YOLOv8Detector
from detector.pose_detector import PoseDetector
from analyzer.ffmpeg import iter_video_frames
from analyzer.swing_analyzer import SwingAnalyzer
from analyzer.trajectory_optimizer import TrajectoryOptimizer
from analyzer.swing_state_machine import SwingStateMachine, SwingPhase


router = APIRouter()

# 简易后台任务存储
_JOB_STORE: Dict[str, Dict] = {}

# 分析结果存储
_ANALYSIS_RESULTS: Dict[str, Dict[str, Any]] = {}

# 转换任务存储
_CONVERSION_JOBS: Dict[str, Dict] = {}

# 服务器资源监控
_SERVER_STATUS = {
    "active_conversions": 0,
    "max_concurrent_conversions": 3,  # 限制并发转换数量
    "server_load": "normal"
}

def _analyze_video_job(job_id: str, video_path: str, resolution: str = "480", confidence: str = "0.01", iou: str = "0.7", max_det: str = "10") -> None:
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
        
        # 处理每一帧，使用用户选择的参数
        resolution_int = int(resolution) if resolution.isdigit() else 480
        confidence_float = float(confidence) if confidence else 0.01
        iou_float = float(iou) if iou else 0.7
        max_det_int = int(max_det) if max_det.isdigit() else 10
        
        print(f"使用分析参数: 分辨率={resolution_int}×{resolution_int}, 置信度={confidence_float}, IoU={iou_float}, 最大检测={max_det_int}")
        for ok, frame_bgr in iter_video_frames(video_path, sample_stride=1, max_size=resolution_int):
            if not ok:
                break
            res = detector.detect_single_point(frame_bgr, imgsz=resolution_int, conf=confidence_float, iou=iou_float, max_det=max_det_int)
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
        
        # 挥杆状态分析
        print("🎯 开始挥杆状态分析...")
        try:
            swing_state_machine = SwingStateMachine()
            swing_phases = swing_state_machine.analyze_swing(norm_trajectory)
            print(f"✅ 挥杆状态分析完成，共分析 {len(swing_phases)} 帧")
        except Exception as e:
            print(f"❌ 挥杆状态分析失败: {e}")
            import traceback
            traceback.print_exc()
            # 使用默认状态
            swing_phases = [SwingPhase.UNKNOWN] * len(norm_trajectory)

        result = {
            "total_frames": total_frames,
            "detected_frames": detected_frames,
            "detection_rate": round(detection_rate, 2),
            "avg_confidence": round(avg_confidence, 3),
            "club_head_trajectory": norm_trajectory,  # 原始轨迹（归一化坐标）
            "optimized_trajectory": optimized_trajectory,  # 标准优化后的轨迹
            "fast_motion_trajectory": fast_motion_trajectory,  # 快速移动优化后的轨迹
            "frame_detections": frame_detections,
            "swing_phases": [phase.value for phase in swing_phases],  # 挥杆状态序列
            "video_info": {
                "width": video_width,
                "height": video_height,
                "fps": video_fps
            }
        }
        _JOB_STORE[job_id]["status"] = "done"
        _JOB_STORE[job_id]["result"] = result
        
        # 生成失败帧下载页面（在删除视频文件之前）
        try:
            # 将失败帧定义为：
            # 1) 条目为 None；或
            # 2) 条目是字典且 detected 为 False；或
            # 3) 归一化坐标为 (0,0)
            failure_frames = []
            for i, det in enumerate(frame_detections):
                if det is None:
                    failure_frames.append(i)
                    continue
                if isinstance(det, dict):
                    if not det.get("detected", False):
                        failure_frames.append(i)
                        continue
                    nx = det.get("norm_x", None)
                    ny = det.get("norm_y", None)
                    if nx == 0 and ny == 0:
                        failure_frames.append(i)
            print(f"检测到 {len(failure_frames)} 个失败帧: {failure_frames[:10]}...")  # 只显示前10个
            if failure_frames:
                print(f"开始生成失败帧下载页面，任务ID: {job_id}")
                failure_download_url = _generate_failure_frames_page(job_id, video_path, failure_frames)
                print(f"失败帧下载页面生成完成: {failure_download_url}")
                # 将下载链接写入结果，确保状态接口能返回给前端
                try:
                    result["failure_download_url"] = failure_download_url
                    _JOB_STORE[job_id]["result"] = result
                except Exception:
                    pass
                _JOB_STORE[job_id]["failure_download_url"] = failure_download_url
            else:
                print("没有失败帧，跳过下载页面生成")
        except Exception as e:
            print(f"生成失败帧下载页面时出错: {e}")
            import traceback
            traceback.print_exc()
            # 不影响主要分析结果
        
        # 删除视频文件
        try:
            os.remove(video_path)
            print(f"已删除临时视频文件: {video_path}")
        except Exception as e:
            print(f"删除临时视频文件失败: {e}")
            
    except Exception as e:
        _JOB_STORE[job_id]["status"] = "error"
        _JOB_STORE[job_id]["error"] = str(e)
        # 即使出错也要删除视频文件
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
        "golftrainer_analysis": {
            "basic_info": {
                "version": 1.0,
                "num_frames": video_spec["num_frames"],
                "video_spec": {
                    "height": video_spec["height"],
                    "width": video_spec["width"],
                    "num_frames": video_spec["num_frames"],
                    "fps": video_spec["fps"],
                    "scale": 100,
                    "rotate": ""
                }
            },
            "mp_result": {
                "landmarks": _get_mp_landmark_names(),
                "landmarks_count": len(_get_mp_landmark_names())
            },
            "pose_result": {
                "poses": poses,
                "handed": "RightHanded" if handed.lower() == "right" else "LeftHanded",
                "poses_count": len(poses)
            },
            "club_head_result": {
                "trajectory_points": optimized_trajectory,  # 修正字段名以匹配Golftrainer格式
                "valid_points_count": trajectory_stats.get("valid_points", len(optimized_trajectory)),
                "total_points_count": trajectory_stats.get("total_points", len(optimized_trajectory))
            },
            "trajectory_analysis": {
                "x_range": {
                    "min": min([p[0] for p in optimized_trajectory if p[0] != 0], default=0.0),
                    "max": max([p[0] for p in optimized_trajectory if p[0] != 0], default=0.0)
                },
                "y_range": {
                    "min": min([p[1] for p in optimized_trajectory if p[1] != 0], default=0.0),
                    "max": max([p[1] for p in optimized_trajectory if p[1] != 0], default=0.0)
                },
                "total_distance": _calculate_trajectory_distance(optimized_trajectory),
                "average_movement_per_frame": _calculate_trajectory_distance(optimized_trajectory) / max(len(optimized_trajectory), 1)
            },
            "data_frames": {
                "mp_data_frame": {
                    "shape": [len(landmarks_list), len(_get_mp_landmark_names()) * 4],  # x,y,visibility,presence
                    "columns_count": len(_get_mp_landmark_names()) * 4,
                    "sample_data": landmarks_list[0][:10] if landmarks_list and landmarks_list[0] else []
                },
                "norm_data_frame": {
                    "shape": [len(landmarks_list), len(_get_mp_landmark_names()) * 2],  # x,y only
                    "columns_count": len(_get_mp_landmark_names()) * 2,
                    "sample_data": [landmarks_list[0][i] for i in range(0, min(10, len(landmarks_list[0])), 2)] if landmarks_list and landmarks_list[0] else []
                }
            },
            "sample_trajectory": {
                "first_20_points": optimized_trajectory[:20]
            }
        }
    }

    # 生成结果ID并存储结果
    result_id = str(uuid.uuid4())
    _ANALYSIS_RESULTS[result_id] = {
        "result": response,
        "timestamp": time.time(),
        "video_info": {
            "filename": file.filename or "video.mp4",
            "width": video_spec["width"],
            "height": video_spec["height"],
            "fps": video_spec["fps"],
            "num_frames": video_spec["num_frames"]
        }
    }
    
    # 添加可视化URL到响应中
    response["visualization_url"] = f"/analyze/visualize/{result_id}"
    
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


def _calculate_trajectory_distance(trajectory: List[List[float]]) -> float:
    """计算轨迹总距离"""
    if len(trajectory) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(1, len(trajectory)):
        prev_point = trajectory[i-1]
        curr_point = trajectory[i]
        
        # 跳过无效点 (0,0)
        if prev_point[0] == 0 and prev_point[1] == 0:
            continue
        if curr_point[0] == 0 and curr_point[1] == 0:
            continue
            
        # 计算欧几里得距离
        dx = curr_point[0] - prev_point[0]
        dy = curr_point[1] - prev_point[1]
        distance = (dx * dx + dy * dy) ** 0.5
        total_distance += distance
    
    return total_distance


def _clean_json_data(data):
    """递归清理JSON数据中的NaN和无穷大值"""
    if isinstance(data, dict):
        return {key: _clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_clean_json_data(item) for item in data]
    elif isinstance(data, float):
        if data != data or data == float('inf') or data == float('-inf'):  # NaN or inf
            return 0.0
        return data
    elif isinstance(data, np.floating):
        if np.isnan(data) or np.isinf(data):
            return 0.0
        return float(data)
    else:
        return data


def _check_video_compatibility(video_path: str) -> dict:
    """检查视频兼容性"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"compatible": False, "error": "无法打开视频文件"}
        
        # 获取视频信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        fourcc_str = ''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        
        cap.release()
        
        # 检查编码格式兼容性
        compatible_formats = ['h264', 'H264', 'avc1', 'AVC1']
        is_compatible = fourcc_str.lower() in [fmt.lower() for fmt in compatible_formats]
        
        return {
            "compatible": is_compatible,
            "video_info": {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "codec": fourcc_str,
                "aspect_ratio": width / height if height > 0 else 0
            },
            "compatibility": {
                "browser_playback": is_compatible,
                "backend_processing": True,
                "recommended_format": "H.264 encoded MP4" if not is_compatible else "Current format is compatible"
            }
        }
        
    except Exception as e:
        return {"compatible": False, "error": str(e)}


@router.get("/visualize/{result_id}")
async def get_visualization_page(result_id: str):
    """返回分析结果可视化页面"""
    if result_id not in _ANALYSIS_RESULTS:
        raise HTTPException(status_code=404, detail="分析结果未找到或已过期")
    
    result_data = _ANALYSIS_RESULTS[result_id]
    analysis_result = result_data["result"]
    video_info = result_data["video_info"]
    
    # 提取轨迹数据
    trajectory_points = analysis_result["golftrainer_analysis"]["club_head_result"]["trajectory_points"]
    
    # 计算Canvas尺寸，保持视频宽高比
    video_width = video_info["width"]
    video_height = video_info["height"]
    video_aspect_ratio = video_width / video_height
    
    # 设置Canvas最大尺寸
    max_canvas_width = 800
    max_canvas_height = 600
    
    # 根据视频宽高比计算Canvas尺寸，保持宽高比
    if video_aspect_ratio > 1:  # 横屏视频
        canvas_width = min(max_canvas_width, int(max_canvas_height * video_aspect_ratio))
        canvas_height = max_canvas_height
    else:  # 竖屏视频
        canvas_height = min(max_canvas_height, int(max_canvas_width / video_aspect_ratio))
        canvas_width = int(canvas_height * video_aspect_ratio)
    
    # 生成可视化页面HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GolfTracker 分析结果可视化</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .video-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .video-info h3 {{
            margin-top: 0;
            color: #333;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .info-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .info-label {{
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
        }}
        .info-value {{
            font-size: 1.2em;
            color: #333;
            margin-top: 5px;
        }}
        .trajectory-section {{
            margin-bottom: 30px;
        }}
        .trajectory-section h3 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .canvas-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .trajectory-canvas {{
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background: #fafafa;
            display: block;
            margin: 0 auto;
        }}
        .canvas-info {{
            margin-top: 10px;
            font-size: 12px;
            color: #666;
            font-family: monospace;
        }}
        .frame-controls {{
            text-align: center;
            margin: 20px 0;
        }}
        .frame-controls button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .frame-controls button:hover {{
            background: #5a6fd8;
        }}
        .frame-controls button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .frame-info {{
            text-align: center;
            margin: 15px 0;
            font-size: 16px;
            color: #666;
        }}
        .json-section {{
            margin-top: 30px;
        }}
        .json-section h3 {{
            color: #333;
            margin-bottom: 15px;
        }}
        .json-container {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .json-content {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            white-space: pre-wrap;
        }}
        .download-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 15px;
        }}
        .download-btn:hover {{
            background: #218838;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏌️ GolfTracker 分析结果</h1>
            <p>视频分析可视化 - {video_info['filename']}</p>
        </div>
        
        <div class="content">
            <div class="video-info">
                <h3>📹 视频信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">文件名</div>
                        <div class="info-value">{video_info['filename']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">分辨率</div>
                        <div class="info-value">{video_info['width']} × {video_info['height']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">帧率</div>
                        <div class="info-value">{video_info['fps']} FPS</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">总帧数</div>
                        <div class="info-value">{video_info['num_frames']} 帧</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(trajectory_points)}</div>
                    <div class="stat-label">轨迹点数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['golftrainer_analysis']['club_head_result']['valid_points_count']}</div>
                    <div class="stat-label">有效检测</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{(analysis_result['golftrainer_analysis']['club_head_result']['valid_points_count'] / analysis_result['golftrainer_analysis']['club_head_result']['total_points_count'] * 100):.1f}%</div>
                    <div class="stat-label">检测率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analysis_result['golftrainer_analysis']['trajectory_analysis']['total_distance']:.2f}</div>
                    <div class="stat-label">总距离</div>
                </div>
            </div>
            
            <div class="trajectory-section">
                <h3>🎯 杆头轨迹可视化</h3>
                <div class="canvas-container">
                    <canvas id="trajectoryCanvas" class="trajectory-canvas" width="{canvas_width}" height="{canvas_height}"></canvas>
                    <div class="canvas-info">
                        <span>视频尺寸: {video_width} × {video_height} | Canvas: {canvas_width} × {canvas_height}</span>
                    </div>
                </div>
                
                <div class="frame-controls">
                    <button id="prevFrame" onclick="changeFrame(-1)">⬅️ 上一帧</button>
                    <button id="playPause" onclick="togglePlay()">▶️ 播放</button>
                    <button id="nextFrame" onclick="changeFrame(1)">下一帧 ➡️</button>
                </div>
                
                <div class="frame-info">
                    <span id="frameInfo">帧 1 / {len(trajectory_points)}</span>
                    <span id="pointInfo" style="margin-left: 20px;"></span>
                </div>
            </div>
            
            <div class="json-section">
                <h3>📄 完整分析结果 (JSON)</h3>
                <button class="download-btn" onclick="downloadJSON()">💾 下载JSON文件</button>
                <div class="json-container">
                    <div class="json-content" id="jsonContent"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 轨迹数据
        const trajectoryData = {json.dumps(trajectory_points, ensure_ascii=False)};
        const videoInfo = {json.dumps(video_info, ensure_ascii=False)};
        const fullResult = {json.dumps(analysis_result, ensure_ascii=False, indent=2)};
        
        // 显示JSON内容
        document.getElementById('jsonContent').textContent = JSON.stringify(fullResult, null, 2);
        
        // 画布设置
        const canvas = document.getElementById('trajectoryCanvas');
        const ctx = canvas.getContext('2d');
        const canvasWidth = {canvas_width};
        const canvasHeight = {canvas_height};
        
        // 设置Canvas实际尺寸
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        
        let currentFrame = 0;
        let isPlaying = false;
        let playInterval;
        
        // 绘制轨迹
        function drawTrajectory() {{
            ctx.clearRect(0, 0, canvasWidth, canvasHeight);
            
            // 绘制背景网格
            ctx.strokeStyle = '#f0f0f0';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 10; i++) {{
                const x = (canvasWidth / 10) * i;
                const y = (canvasHeight / 10) * i;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvasHeight);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvasWidth, y);
                ctx.stroke();
            }}
            
            // 绘制完整轨迹线
            ctx.strokeStyle = '#e0e0e0';
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let i = 0; i < trajectoryData.length; i++) {{
                const point = trajectoryData[i];
                if (point[0] !== 0 || point[1] !== 0) {{
                    const x = point[0] * canvasWidth;
                    const y = point[1] * canvasHeight;
                    if (i === 0) {{
                        ctx.moveTo(x, y);
                    }} else {{
                        ctx.lineTo(x, y);
                    }}
                }}
            }}
            ctx.stroke();
            
            // 绘制已走过的轨迹（高亮）
            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 3;
            ctx.beginPath();
            for (let i = 0; i <= currentFrame; i++) {{
                const point = trajectoryData[i];
                if (point[0] !== 0 || point[1] !== 0) {{
                    const x = point[0] * canvasWidth;
                    const y = point[1] * canvasHeight;
                    if (i === 0) {{
                        ctx.moveTo(x, y);
                    }} else {{
                        ctx.lineTo(x, y);
                    }}
                }}
            }}
            ctx.stroke();
            
            // 绘制当前帧的点
            if (currentFrame < trajectoryData.length) {{
                const point = trajectoryData[currentFrame];
                if (point[0] !== 0 || point[1] !== 0) {{
                    const x = point[0] * canvasWidth;
                    const y = point[1] * canvasHeight;
                    
                    // 绘制大圆点
                    ctx.fillStyle = '#ff4757';
                    ctx.beginPath();
                    ctx.arc(x, y, 8, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // 绘制边框
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }}
            }}
            
            // 更新信息显示
            document.getElementById('frameInfo').textContent = `帧 ${{currentFrame + 1}} / ${{trajectoryData.length}}`;
            if (currentFrame < trajectoryData.length) {{
                const point = trajectoryData[currentFrame];
                if (point[0] !== 0 || point[1] !== 0) {{
                    document.getElementById('pointInfo').textContent = `位置: (${{point[0].toFixed(3)}}, ${{point[1].toFixed(3)}})`;
                }} else {{
                    document.getElementById('pointInfo').textContent = '未检测到杆头';
                }}
            }}
        }}
        
        // 切换帧
        function changeFrame(delta) {{
            currentFrame = Math.max(0, Math.min(trajectoryData.length - 1, currentFrame + delta));
            drawTrajectory();
        }}
        
        // 播放/暂停
        function togglePlay() {{
            if (isPlaying) {{
                clearInterval(playInterval);
                isPlaying = false;
                document.getElementById('playPause').textContent = '▶️ 播放';
            }} else {{
                isPlaying = true;
                document.getElementById('playPause').textContent = '⏸️ 暂停';
                playInterval = setInterval(() => {{
                    if (currentFrame < trajectoryData.length - 1) {{
                        currentFrame++;
                        drawTrajectory();
                    }} else {{
                        togglePlay();
                    }}
                }}, 100); // 100ms间隔
            }}
        }}
        
        // 下载JSON
        function downloadJSON() {{
            const dataStr = JSON.stringify(fullResult, null, 2);
            const dataBlob = new Blob([dataStr], {{type: 'application/json'}});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'golftracker_analysis_result.json';
            link.click();
            URL.revokeObjectURL(url);
        }}
        
        // 初始化
        drawTrajectory();
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)


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
            
            <!-- 视频转换服务入口 -->
            <div style="margin-top: 15px; padding: 16px 20px; border: 2px solid #667eea; border-radius: 10px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                    <div style="flex: 1; min-width: 300px;">
                        <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 16px; font-weight: 600;">
                            🎥 视频格式转换服务
                        </h3>
                        <p style="margin: 0; color: #495057; font-size: 14px; line-height: 1.5;">
                            如果您的视频文件格式不兼容或无法正常播放，可以使用我们的转换服务将视频转换为H.264格式
                        </p>
                    </div>
                    <div style="flex-shrink: 0;">
                        <a href="/convert/test-page" target="_blank" 
                           style="display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #667eea, #764ba2); 
                                  color: white; text-decoration: none; border-radius: 20px; font-weight: 600; 
                                  transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);"
                           onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'"
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.3)'">
                            🚀 转换视频格式
                        </a>
                    </div>
                </div>
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
    <script src="/static/js/trajectory-module.js?v=1.7"></script>
    <script src="/static/js/video-player-module.js?v=2.2"></script>
    <script src="/static/js/json-output-module.js?v=1.8"></script>
    <script src="/static/js/frame-analysis-module.js?v=1.6"></script>
    <script src="/static/js/swing-visualization-module.js?v=1.0"></script>
    <script src="/static/js/main.js?v=1.6"></script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.post("/video")
async def analyze_video_test(
    video: UploadFile = File(...), 
    resolution: str = Form("480"),
    confidence: str = Form("0.01"),
    iou: str = Form("0.7"),
    max_det: str = Form("10")
):
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

        # 检查视频兼容性
        compatibility_info = _check_video_compatibility(tmp_path)
        print(f"视频兼容性检查: {compatibility_info}")

        # 后台任务：生成 job_id 并启动线程处理
        job_id = str(uuid.uuid4())
        _JOB_STORE[job_id] = {
            "status": "queued", 
            "progress": 0, 
            "filename": video.filename,
            "compatibility": compatibility_info,
            "resolution": resolution,
            "confidence": confidence,
            "iou": iou,
            "max_det": max_det
        }
        t = threading.Thread(target=_analyze_video_job, args=(job_id, tmp_path, resolution, confidence, iou, max_det), daemon=True)
        t.start()
        
        response = {
            "job_id": job_id, 
            "status": "queued",
            "compatibility": compatibility_info
        }
        
        # 如果不兼容，添加警告信息和转换服务链接
        if not compatibility_info.get("compatible", True):
            response["warning"] = {
                "message": "检测到视频格式可能不兼容浏览器播放",
                "codec": compatibility_info.get("video_info", {}).get("codec", "unknown"),
                "recommendation": "建议使用H.264编码的MP4文件以获得最佳兼容性",
                "conversion_service": {
                    "available": True,
                    "url": "/convert/test-page",
                    "description": "使用我们的转换服务将视频转换为兼容格式"
                }
            }
        
        return response
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/video/status")
async def analyze_video_status(job_id: str):
    job = _JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") == "done":
        # 清理结果中的NaN和无穷大值
        result = job.get("result", {})
        cleaned_result = _clean_json_data(result)
        return {"job_id": job_id, "status": "done", "result": cleaned_result}
    if job.get("status") == "error":
        return {"job_id": job_id, "status": "error", "error": job.get("error")}
    return {"job_id": job_id, "status": job.get("status"), "progress": job.get("progress", 0)}


@router.get("/supported-formats")
async def get_supported_formats():
    """返回支持的视频格式信息"""
    return {
        "title": "GolfTracker 支持的视频格式",
        "description": "查看支持的视频格式和编码要求",
        "compatible_formats": {
            "H.264": {
                "description": "最广泛支持的编码格式",
                "file_extensions": [".mp4", ".mov"],
                "browser_support": "优秀",
                "recommended": True
            },
            "AVC1": {
                "description": "H.264的变体，兼容性良好",
                "file_extensions": [".mp4"],
                "browser_support": "优秀",
                "recommended": True
            }
        },
        "incompatible_formats": {
            "FMP4": {
                "description": "分片MP4格式，浏览器支持有限",
                "file_extensions": [".mov", ".mp4"],
                "browser_support": "差",
                "solution": "需要转换为H.264"
            },
            "H.265": {
                "description": "新一代编码格式，浏览器支持有限",
                "file_extensions": [".mp4", ".mov"],
                "browser_support": "一般",
                "solution": "需要转换为H.264"
            },
            "VP9": {
                "description": "Google开发的编码格式",
                "file_extensions": [".webm", ".mp4"],
                "browser_support": "一般",
                "solution": "需要转换为H.264"
            }
        },
        "recommended_settings": {
            "video_codec": "H.264 (libx264)",
            "audio_codec": "AAC",
            "container": "MP4",
            "resolution": "720p 或 1080p",
            "frame_rate": "30fps",
            "quality": "中等质量"
        },
        "conversion_service": {
            "available": True,
            "endpoint": "/convert/video",
            "description": "使用我们的转换服务将不兼容的视频转换为H.264格式"
        }
    }


@router.get("/conversion-guide")
async def get_conversion_guide():
    """返回视频转换指导信息"""
    return {
        "title": "GolfTracker 视频格式转换指导",
        "description": "将不兼容的视频格式转换为H.264编码的MP4格式",
        "conversion_service": {
            "name": "GolfTracker转换服务",
            "description": "使用我们的专用转换服务",
            "endpoint": "/convert/video",
            "pros": ["专用服务", "高质量转换", "无需安装软件", "快速处理"],
            "cons": ["需要重新上传", "服务器资源消耗"]
        },
        "external_methods": [
            {
                "name": "在线转换工具",
                "description": "使用第三方在线转换工具",
                "tools": [
                    "CloudConvert (https://cloudconvert.com/mov-to-mp4)",
                    "Convertio (https://convertio.co/mov-mp4/)",
                    "Online-Convert (https://www.online-convert.com/)"
                ],
                "pros": ["无需安装软件", "简单易用"],
                "cons": ["需要上传文件", "网络依赖", "隐私考虑"]
            },
            {
                "name": "桌面软件",
                "description": "使用免费桌面转换软件",
                "tools": ["VLC Media Player", "HandBrake", "QuickTime Player"],
                "pros": ["本地处理", "隐私安全", "完全控制"],
                "cons": ["需要安装软件", "学习成本"]
            }
        ],
        "recommended_settings": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "quality": "medium (crf 23)",
            "preset": "medium",
            "web_optimization": "movflags +faststart"
        },
        "compatible_formats": ["H.264", "AVC1"],
        "incompatible_formats": ["FMP4", "H.265", "VP9"],
        "troubleshooting": {
            "conversion_failed": "检查FFmpeg安装和文件权限",
            "file_too_large": "降低质量设置或分辨率",
            "playback_issues": "确认输出格式为H.264 MP4"
        }
    }


def _generate_failure_frames_page(job_id: str, video_path: str, failure_frames: List[int]) -> str:
    """生成失败帧下载页面并返回URL"""
    try:
        print(f"开始处理视频: {video_path}")
        # 打开视频获取失败帧的图片
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return None
        
        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"视频信息: 总帧数={total_frames}, FPS={fps}")
        
        # 收集失败帧数据
        failure_frame_data = []
        print(f"开始处理 {len(failure_frames)} 个失败帧...")
        for i, frame_num in enumerate(failure_frames):
            if i % 5 == 0:  # 每5帧打印一次进度
                print(f"处理进度: {i+1}/{len(failure_frames)} (帧 {frame_num})")
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if ret:
                # 将帧转换为base64编码的图片
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                failure_frame_data.append({
                    "frame_number": frame_num,
                    "timestamp": frame_num / fps,
                    "image_data": img_base64,
                    "filename": f"failure_frame_{frame_num:03d}.jpg"
                })
            else:
                print(f"警告: 无法读取第 {frame_num} 帧")
        
        cap.release()
        
        if not failure_frame_data:
            print("没有成功提取到失败帧数据")
            return None
        
        print(f"成功提取 {len(failure_frame_data)} 个失败帧，开始生成HTML...")
        
        # 生成HTML内容
        html_content = _generate_failure_frames_html(failure_frame_data, job_id, len(failure_frames), total_frames)
        print("HTML内容生成完成")
        
        # 保存HTML文件
        html_filename = f"failure_frames_{job_id}.html"
        html_path = os.path.join("static", html_filename)
        
        # 确保static目录存在
        os.makedirs("static", exist_ok=True)
        print(f"保存HTML文件到: {html_path}")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML文件保存完成，返回URL: /static/{html_filename}")
        return f"/static/{html_filename}"
        
    except Exception as e:
        print(f"生成失败帧下载页面失败: {e}")
        return None


def _generate_failure_frames_html(failure_frame_data: List[Dict], job_id: str, failure_count: int, total_frames: int) -> str:
    """生成失败帧下载页面的HTML内容"""
    
    failure_rate = (failure_count / total_frames) * 100
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>检测失败帧下载 - Job {job_id[:8]}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.2em;
        }}
        
        .summary {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 4px solid #dc3545;
        }}
        
        .summary h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .summary p {{
            margin: 5px 0;
            color: #495057;
        }}
        
        .failure-rate {{
            font-size: 1.2em;
            font-weight: bold;
            color: #dc3545;
        }}
        
        .controls {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin: 0 10px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: linear-gradient(135deg, #6c757d, #495057);
        }}
        
        .frames-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .frame-item {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
        }}
        
        .frame-item:hover {{
            border-color: #667eea;
            transform: translateY(-2px);
        }}
        
        .frame-item.selected {{
            border-color: #28a745;
            background: #f8fff9;
        }}
        
        .frame-image {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        
        .frame-info {{
            text-align: center;
        }}
        
        .frame-info h4 {{
            margin: 0 0 5px 0;
            color: #2c3e50;
        }}
        
        .frame-info p {{
            margin: 0;
            color: #6c757d;
            font-size: 14px;
        }}
        
        .download-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
            transition: all 0.3s ease;
        }}
        
        .download-btn:hover {{
            background: #218838;
            transform: translateY(-1px);
        }}
        
        .select-all {{
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .select-all input[type="checkbox"] {{
            margin-right: 10px;
            transform: scale(1.2);
        }}
        
        .select-all label {{
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 检测失败帧下载工具</h1>
        
        <div class="summary">
            <h3>📊 检测统计</h3>
            <p><strong>任务ID:</strong> {job_id}</p>
            <p><strong>总帧数:</strong> {total_frames} 帧</p>
            <p><strong>失败帧数量:</strong> {failure_count} 帧</p>
            <p><strong>失败率:</strong> <span class="failure-rate">{failure_rate:.1f}%</span></p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>用途:</strong> 这些图片可用于模型训练数据增强，提高杆头检测准确率</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="selectAll()">全选所有帧</button>
            <button class="btn btn-secondary" onclick="clearSelection()">清除选择</button>
            <button class="btn" onclick="downloadSelected()">下载选中帧</button>
            <a href="/analyze/server-test" class="btn btn-secondary">返回主页面</a>
        </div>
        
        <div class="select-all">
            <input type="checkbox" id="selectAllCheckbox" onchange="toggleAllSelection()">
            <label for="selectAllCheckbox">全选/取消全选</label>
        </div>
        
        <div class="frames-grid">
"""
    
    # 添加每个失败帧
    for i, frame_data in enumerate(failure_frame_data):
        html += f"""
            <div class="frame-item" data-frame="{frame_data['frame_number']}">
                <img src="data:image/jpeg;base64,{frame_data['image_data']}" 
                     alt="Frame {frame_data['frame_number']}" 
                     class="frame-image">
                <div class="frame-info">
                    <h4>第 {frame_data['frame_number']} 帧</h4>
                    <p>时间: {frame_data['timestamp']:.2f}s</p>
                    <p>文件名: {frame_data['filename']}</p>
                    <button class="download-btn" onclick="downloadSingleFrame({i})">
                        下载此帧
                    </button>
                </div>
            </div>
        """
    
    html += """
        </div>
    </div>

    <script>
        const failureFrames = """ + json.dumps(failure_frame_data) + """;
        
        function selectAll() {
            const items = document.querySelectorAll('.frame-item');
            items.forEach(item => {
                item.classList.add('selected');
            });
            document.getElementById('selectAllCheckbox').checked = true;
        }
        
        function clearSelection() {
            const items = document.querySelectorAll('.frame-item');
            items.forEach(item => {
                item.classList.remove('selected');
            });
            document.getElementById('selectAllCheckbox').checked = false;
        }
        
        function toggleAllSelection() {
            const checkbox = document.getElementById('selectAllCheckbox');
            if (checkbox.checked) {
                selectAll();
            } else {
                clearSelection();
            }
        }
        
        function downloadSingleFrame(index) {
            const frame = failureFrames[index];
            downloadFrame(frame);
        }
        
        function downloadSelected() {
            const selectedItems = document.querySelectorAll('.frame-item.selected');
            if (selectedItems.length === 0) {
                alert('请先选择要下载的帧！');
                return;
            }
            
            selectedItems.forEach(item => {
                const frameNumber = parseInt(item.dataset.frame);
                const frame = failureFrames.find(f => f.frame_number === frameNumber);
                if (frame) {
                    downloadFrame(frame);
                }
            });
        }
        
        function downloadFrame(frame) {
            // 创建下载链接
            const link = document.createElement('a');
            link.href = 'data:image/jpeg;base64,' + frame.image_data;
            link.download = frame.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        // 点击帧项目切换选择状态
        document.addEventListener('click', function(e) {
            if (e.target.closest('.frame-item') && !e.target.closest('.download-btn')) {
                const item = e.target.closest('.frame-item');
                item.classList.toggle('selected');
                updateSelectAllCheckbox();
            }
        });
        
        function updateSelectAllCheckbox() {
            const totalItems = document.querySelectorAll('.frame-item').length;
            const selectedItems = document.querySelectorAll('.frame-item.selected').length;
            const checkbox = document.getElementById('selectAllCheckbox');
            
            if (selectedItems === 0) {
                checkbox.checked = false;
                checkbox.indeterminate = false;
            } else if (selectedItems === totalItems) {
                checkbox.checked = true;
                checkbox.indeterminate = false;
            } else {
                checkbox.checked = false;
                checkbox.indeterminate = true;
            }
        }
    </script>
</body>
</html>
"""
    
    return html
