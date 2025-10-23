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
        
        try:
            # 从analyze.py导入全局变量
            from app.routes.analyze import _JOB_STORE
            
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
            
            # 动态分辨率处理：根据视频实际尺寸调整分析分辨率
            confidence_float = float(confidence) if confidence else 0.01
            iou_float = float(iou) if iou else 0.7
            max_det_int = int(max_det) if max_det.isdigit() else 10
            
            # 计算动态分辨率：使用视频长边作为分析分辨率，但限制在合理范围内
            video_long_edge = max(video_width, video_height)
            # 从配置中获取分辨率限制
            from app.config import VIDEO_ANALYSIS_CONFIG
            min_resolution = VIDEO_ANALYSIS_CONFIG.get("resolution_limits", {}).get("min", 480)
            max_resolution = VIDEO_ANALYSIS_CONFIG.get("resolution_limits", {}).get("max", 1920)
            # 限制分辨率范围
            dynamic_resolution = max(min_resolution, min(max_resolution, video_long_edge))
            
            # 如果用户指定了分辨率且不是"auto"，则使用用户指定的分辨率
            if resolution and resolution != "auto" and resolution.isdigit():
                user_resolution = int(resolution)
                # 用户指定的分辨率也要在合理范围内
                dynamic_resolution = max(min_resolution, min(max_resolution, user_resolution))
            
            print(f"🎯 视频分析参数:")
            print(f"   原始视频尺寸: {video_width}×{video_height}")
            print(f"   实际分析分辨率: {dynamic_resolution}×{dynamic_resolution}")
            print(f"   检测参数: 置信度={confidence_float}, IoU={iou_float}, 最大检测={max_det_int}")
            print(f"   优化策略: {optimization_strategy}")
            
            for ok, frame_bgr in iter_video_frames(video_path, sample_stride=1, max_size=dynamic_resolution):
                if not ok:
                    break
                res = detector.detect_single_point(frame_bgr, imgsz=dynamic_resolution, conf=confidence_float, iou=iou_float, max_det=max_det_int)
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
            
            # ===== 处理流程：YOLOv8原始检测 → 策略优化 → 双画面对比 =====
            print(f"🎯 开始轨迹优化处理，用户选择策略: {optimization_strategy}")
            
            # 1. 保存原始YOLOv8检测结果（用于左画面）
            original_trajectory = norm_trajectory.copy()
            print(f"📊 原始轨迹数据: {len(original_trajectory)} 个点")
            
            # 2. 初始化策略管理器
            trajectory_optimizer = TrajectoryOptimizer()
            available_strategies = trajectory_optimizer.get_available_strategies()
            
            # 3. 为所有策略生成轨迹（用于对比和选择）
            strategy_trajectories = {}
            strategy_trajectories["original"] = original_trajectory  # 原始检测结果
            
            print(f"🔄 开始生成所有策略轨迹...")
            print(f"🔄 可用策略: {list(available_strategies.keys())}")
            for strategy_id, strategy_info in available_strategies.items():
                # 处理所有策略，不只是real_开头的
                if strategy_id != "original":  # 跳过原始检测
                    try:
                        print(f"  🔍 处理策略: {strategy_info.name} (ID: {strategy_id})")
                        trajectory = trajectory_optimizer.optimize_with_strategy(norm_trajectory, strategy_id)
                        print(f"  🔍 策略 {strategy_id} 返回轨迹长度: {len(trajectory)}")
                        strategy_trajectories[strategy_id] = clean_trajectory(trajectory)
                        print(f"  ✅ 策略 {strategy_info.name} 生成成功")
                    except Exception as e:
                        print(f"  ❌ 策略 {strategy_id} 生成失败: {e}")
                        import traceback
                        traceback.print_exc()
                        strategy_trajectories[strategy_id] = original_trajectory  # 失败时使用原始数据
            
            # 4. 确定用户选择的最终轨迹（用于右画面）
            if optimization_strategy == "original":
                final_trajectory = original_trajectory
                strategy_name = "原始检测"
            else:
                final_trajectory = strategy_trajectories.get(optimization_strategy, original_trajectory)
                strategy_info = available_strategies.get(optimization_strategy)
                strategy_name = strategy_info.name if strategy_info else optimization_strategy
            
            print(f"🎯 最终选择: {strategy_name} (轨迹长度: {len(final_trajectory)})")
            
            # 为了向后兼容，保留原有的轨迹字段
            optimized_trajectory = strategy_trajectories.get('real_trajectory_optimization', norm_trajectory)
            
            # 使用快速移动优化器（从策略中获取）
            fast_motion_trajectory = strategy_trajectories.get('real_fast_motion', original_trajectory)
            
            # 挥杆状态分析（使用右画面的最终轨迹，包含补齐/平滑，Top 更稳）
            print("🎯 开始挥杆状态分析...")
            try:
                swing_state_machine = SwingStateMachine()
                swing_phases = swing_state_machine.analyze_swing(final_trajectory)
                print(f"✅ 挥杆状态分析完成，共分析 {len(swing_phases)} 帧")
            except Exception as e:
                print(f"❌ 挥杆状态分析失败: {e}")
                import traceback
                traceback.print_exc()
                # 使用默认状态
                swing_phases = [SwingPhase.UNKNOWN] * len(norm_trajectory)

            # 5. 生成补齐后的frame_detections数据（用于右画面显示）
            print(f"🔍 开始生成filled_frame_detections，总帧数: {total_frames}")
            print(f"🔍 final_trajectory长度: {len(final_trajectory)}")
            print(f"🔍 frame_detections长度: {len(frame_detections)}")
            print(f"🔍 final_trajectory前10个点: {final_trajectory[:10]}")
            print(f"🔍 final_trajectory第17个点: {final_trajectory[17] if len(final_trajectory) > 17 else '不存在'}")
            
            filled_frame_detections = []
            for i in range(total_frames):
                original_detection = frame_detections[i] if i < len(frame_detections) else None
                
                if original_detection and original_detection.get("detected", False):
                    # 原始检测成功，使用原始数据
                    filled_frame_detections.append(original_detection)
                else:
                    # 原始检测失败，使用补齐的数据
                    if i < len(final_trajectory):
                        point = final_trajectory[i]
                        if i == 17:  # 特别调试第17帧
                            print(f"🔍 处理第17帧: point={point}")
                        if point and point[0] != 0 and point[1] != 0:
                            # 将归一化坐标转换为像素坐标
                            pixel_x = int(point[0] * video_width)
                            pixel_y = int(point[1] * video_height)
                            
                            filled_frame_detections.append({
                                "frame": i,
                                "detected": True,
                                "x": pixel_x,
                                "y": pixel_y,
                                "confidence": 0.5,  # 补齐的数据给一个中等置信度
                                "norm_x": point[0],
                                "norm_y": point[1],
                                "is_filled": True  # 标记为补齐的数据
                            })
                        else:
                            # 没有补齐数据
                            filled_frame_detections.append({
                                "frame": i,
                                "detected": False,
                                "x": 0,
                                "y": 0,
                                "confidence": 0.0,
                                "norm_x": 0.0,
                                "norm_y": 0.0,
                                "is_filled": False
                            })
                    else:
                        # 超出轨迹长度
                        filled_frame_detections.append({
                            "frame": i,
                            "detected": False,
                            "x": 0,
                            "y": 0,
                            "confidence": 0.0,
                            "norm_x": 0.0,
                            "norm_y": 0.0,
                            "is_filled": False
                        })

            # 统计补齐效果
            filled_count = sum(1 for d in filled_frame_detections if d.get("is_filled", False))
            detected_count = sum(1 for d in filled_frame_detections if d.get("detected", False))
            print(f"✅ filled_frame_detections生成完成:")
            print(f"   - 总帧数: {len(filled_frame_detections)}")
            print(f"   - 检测到帧数: {detected_count}")
            print(f"   - 补齐帧数: {filled_count}")
            print(f"   - 前5帧示例: {filled_frame_detections[:5]}")

        # 6. 构建结果字典，明确双画面数据来源
            result = {
                "total_frames": total_frames,
                "detected_frames": detected_frames,
                "detection_rate": round(detection_rate, 2),
                "avg_confidence": round(avg_confidence, 3),
                
                # ===== 双画面数据 =====
                "left_view_trajectory": original_trajectory,    # 左画面：永远显示原始YOLOv8检测结果
                "right_view_trajectory": final_trajectory,      # 右画面：用户选择的策略结果
                "left_frame_detections": frame_detections,      # 左画面：原始检测数据
                "right_frame_detections": filled_frame_detections, # 右画面：补齐后的检测数据
                
                # ===== 向后兼容字段 =====
                "club_head_trajectory": final_trajectory,       # 用户选择的最终轨迹
                "original_trajectory": original_trajectory,     # 原始轨迹（归一化坐标）
                "optimized_trajectory": optimized_trajectory,   # 标准优化后的轨迹
                "fast_motion_trajectory": fast_motion_trajectory, # 快速移动优化后的轨迹
                
                # ===== 策略相关数据 =====
                "strategy_trajectories": strategy_trajectories, # 所有策略的轨迹
                "available_strategies": available_strategies,   # 可用策略信息
                "selected_strategy": {
                    "id": optimization_strategy,
                    "name": strategy_name
                },
                
                # ===== 其他数据 =====
                "frame_detections": frame_detections,  # 保持向后兼容
                "swing_phases": [phase.value for phase in swing_phases],  # 挥杆状态序列
                
                # ===== 分析参数信息 =====
                "analysis_resolution": f"{dynamic_resolution}×{dynamic_resolution}",
                "video_width": video_width,
                "video_height": video_height,
                "analysis_params": {
                    "resolution": dynamic_resolution,
                    "confidence": confidence_float,
                    "iou": iou_float,
                    "max_det": max_det_int,
                    "optimization_strategy": optimization_strategy
                },
                "video_info": {
                    "width": video_width,
                    "height": video_height,
                    "fps": video_fps
                }
            }
            _JOB_STORE[job_id]["status"] = "done"
            _JOB_STORE[job_id]["result"] = result
            
            # 生成训练数据收集页面（失败帧 + 低置信度帧）
            try:
                # 定义失败帧和低置信度帧
                failure_frames = []
                low_confidence_frames = []
                confidence_threshold = 0.3  # 低置信度阈值
                
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
                        conf = det.get("confidence", 0.0)
                        
                        if nx == 0 and ny == 0:
                            failure_frames.append(i)
                        elif conf < confidence_threshold:
                            low_confidence_frames.append(i)
                
                print(f"检测到 {len(failure_frames)} 个失败帧: {failure_frames[:10]}...")
                print(f"检测到 {len(low_confidence_frames)} 个低置信度帧: {low_confidence_frames[:10]}...")
                
                if failure_frames or low_confidence_frames:
                    print(f"开始生成训练数据收集页面，任务ID: {job_id}")
                    # 使用html_generator_service生成训练数据页面
                    from app.services.html_generator import html_generator_service
                    training_data_url = html_generator_service.generate_training_data_page(
                        job_id, video_path, failure_frames, low_confidence_frames, confidence_threshold
                    )
                    print(f"训练数据收集页面生成完成: {training_data_url}")
                    # 将下载链接写入结果，确保状态接口能返回给前端
                    try:
                        result["training_data_url"] = training_data_url
                        _JOB_STORE[job_id]["result"] = result
                    except Exception:
                        pass
                    _JOB_STORE[job_id]["training_data_url"] = training_data_url
                else:
                    print("没有失败帧或低置信度帧，跳过训练数据收集页面生成")
            except Exception as e:
                print(f"生成训练数据收集页面时出错: {e}")
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
            from app.routes.analyze import _JOB_STORE
            _JOB_STORE[job_id]["status"] = "error"
            _JOB_STORE[job_id]["error"] = str(e)
            # 即使出错也要删除视频文件
            try:
                os.remove(video_path)
            except Exception:
                pass
    
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