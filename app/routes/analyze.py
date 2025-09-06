from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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
from app.services.html_generator import html_generator_service
from app.services.video_analysis import video_analysis_service
from app.services.task_manager import task_manager
from app.services.file_service import file_service
from app.services.video_processing import video_processing_service
from app.services.logging_service import logging_service
from app.services.response_service import response_service
from app.config import SERVER_CONFIG, VIDEO_ANALYSIS_CONFIG


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
    "max_concurrent_conversions": SERVER_CONFIG["max_concurrent_conversions"],
    "server_load": SERVER_CONFIG["default_server_load"]
}

# _analyze_video_job 函数已重构到 video_analysis_service


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

        # 轨迹优化 - 使用策略管理库
        trajectory_optimizer = TrajectoryOptimizer()
        
        # 标准优化
        optimized_trajectory, quality_scores = trajectory_optimizer.optimize_trajectory(trajectory)
        trajectory_stats = trajectory_optimizer.get_trajectory_statistics(optimized_trajectory)
        
        # 快速移动优化
        fast_motion_trajectory, _ = trajectory_optimizer.optimize_with_strategy(trajectory, "fast_motion")
        
        # 获取所有可用策略信息
        available_strategies = trajectory_optimizer.get_available_strategies()

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
                "landmarks": get_mp_landmark_names(),
                "landmarks_count": len(get_mp_landmark_names())
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
                "total_distance": calculate_trajectory_distance(optimized_trajectory),
                "average_movement_per_frame": calculate_trajectory_distance(optimized_trajectory) / max(len(optimized_trajectory), 1)
            },
            "data_frames": {
                "mp_data_frame": {
                    "shape": [len(landmarks_list), len(get_mp_landmark_names()) * 4],  # x,y,visibility,presence
                    "columns_count": len(get_mp_landmark_names()) * 4,
                    "sample_data": landmarks_list[0][:10] if landmarks_list and landmarks_list[0] else []
                },
                "norm_data_frame": {
                    "shape": [len(landmarks_list), len(get_mp_landmark_names()) * 2],  # x,y only
                    "columns_count": len(get_mp_landmark_names()) * 2,
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


@router.get("/strategies")
async def get_strategies():
    """获取所有可用策略"""
    try:
        strategy_manager = get_strategy_manager()
        # 只注册真实策略
        from analyzer.real_strategies import register_real_strategies
        register_real_strategies(strategy_manager)
        
        strategies = strategy_manager.get_all_strategies()
        return {"strategies": strategies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")

@router.get("/strategies/{category}")
async def get_strategies_by_category(category: str):
    """按类别获取策略"""
    try:
        strategy_manager = get_strategy_manager()
        # 只注册真实策略
        from analyzer.real_strategies import register_real_strategies
        register_real_strategies(strategy_manager)
        
        strategies = strategy_manager.get_strategies_by_category(category)
        return {"strategies": strategies, "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")

@router.get("/strategy-test")
async def get_strategy_test_page():
    """返回策略管理测试页面"""
    try:
        with open("static/strategy_test.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="策略测试页面未找到")

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
            
            <!-- 策略管理入口 -->
            <div style="margin-top: 15px; padding: 16px 20px; border: 2px solid #28a745; border-radius: 10px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                    <div style="flex: 1; min-width: 300px;">
                        <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 16px; font-weight: 600;">
                            ⚙️ 轨迹优化策略管理
                        </h3>
                        <p style="margin: 0; color: #495057; font-size: 14px; line-height: 1.5;">
                            管理和对比不同的轨迹优化算法，包括Savitzky-Golay滤波、卡尔曼滤波、线性插值等
                        </p>
                    </div>
                    <div style="flex-shrink: 0; display: flex; gap: 10px;">
                        <a href="/analyze/strategy-test" target="_blank" 
                           style="display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #28a745, #20c997); 
                                  color: white; text-decoration: none; border-radius: 20px; font-weight: 600; 
                                  transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);"
                           onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(40, 167, 69, 0.4)'"
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(40, 167, 69, 0.3)'">
                            🎯 策略管理UI
                        </a>
                        <a href="/analyze/strategies" target="_blank" 
                           style="display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #6c757d, #495057); 
                                  color: white; text-decoration: none; border-radius: 20px; font-weight: 600; 
                                  transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);"
                           onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(108, 117, 125, 0.4)'"
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(108, 117, 125, 0.3)'">
                            📊 API数据
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
            <script src="/static/js/upload-module.js?v=1.8"></script>
    <script src="/static/js/results-module.js?v=1.6"></script>
    <script src="/static/js/trajectory-module.js?v=1.7"></script>
    <script src="/static/js/video-player-module.js?v=2.2"></script>
    <script src="/static/js/json-output-module.js?v=1.8"></script>
    <script src="/static/js/frame-analysis-module.js?v=1.6"></script>
    <script src="/static/js/swing-visualization-module.js?v=1.0"></script>
    <script src="/static/js/dual-player-module.js?v=1.5"></script>
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
    max_det: str = Form("10"),
    optimization_strategy: str = Form("original")
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
        compatibility_info = check_video_compatibility(tmp_path)
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
            "max_det": max_det,
            "optimization_strategy": optimization_strategy
        }
        t = threading.Thread(target=video_analysis_service.analyze_video_job, args=(job_id, tmp_path, resolution, confidence, iou, max_det, optimization_strategy), daemon=True)
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
        cleaned_result = clean_json_data(result)
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


# _generate_training_data_page 函数已重构到 html_generator_service


# _generate_failure_frames_page 函数已重构到 html_generator_service


# _generate_training_data_html 函数已重构到 html_generator_service


@router.get("/training-data/zip/{job_id}")
async def download_training_data_zip(job_id: str):
    """下载训练数据ZIP包"""
    try:
        # 检查任务是否存在
        if job_id not in _JOB_STORE:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        job_data = _JOB_STORE[job_id]
        if job_data["status"] != "done":
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        result = job_data.get("result", {})
        if not result:
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        # 获取训练数据信息
        failure_frames = result.get("failure_frames", [])
        low_confidence_frames = result.get("low_confidence_frames", [])
        total_frames = result.get("total_frames", 0)
        
        if not failure_frames and not low_confidence_frames:
            raise HTTPException(status_code=404, detail="没有训练数据可下载")
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 添加README文件
            readme_content = f"""# 训练数据收集包

## 基本信息
- 任务ID: {job_id}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 总帧数: {total_frames}
- 失败帧数: {len(failure_frames)}
- 低置信度帧数: {len(low_confidence_frames)}
- 总训练帧数: {len(failure_frames) + len(low_confidence_frames)}

## 文件说明
- failure_frame_XXX.jpg: 检测失败的帧图片
- low_confidence_frame_XXX.jpg: 低置信度检测的帧图片

## 用途
这些图片可用于模型训练数据增强，提高杆头检测准确率。

## 建议
1. 对失败帧进行重新标注，作为负样本训练
2. 对低置信度帧进行质量评估，可能需要重新标注
3. 结合原始视频进行上下文分析
"""
            zip_file.writestr("README.txt", readme_content)
            
            # 添加统计信息JSON文件
            stats = {
                "job_id": job_id,
                "generation_time": datetime.now().isoformat(),
                "total_frames": total_frames,
                "failure_frames": failure_frames,
                "low_confidence_frames": low_confidence_frames,
                "failure_count": len(failure_frames),
                "low_confidence_count": len(low_confidence_frames),
                "total_training_frames": len(failure_frames) + len(low_confidence_frames),
                "failure_rate": (len(failure_frames) / total_frames * 100) if total_frames > 0 else 0,
                "low_confidence_rate": (len(low_confidence_frames) / total_frames * 100) if total_frames > 0 else 0
            }
            zip_file.writestr("statistics.json", json.dumps(stats, indent=2, ensure_ascii=False))
            
            # 添加帧图片
            # 注意：这里我们需要重新从视频中提取帧，因为原始视频可能已被删除
            # 为了简化，我们返回一个说明文件
            info_content = f"""注意：由于视频文件已被处理，无法直接生成ZIP包中的图片文件。
请使用训练数据收集页面 (training_data_{job_id}.html) 来下载具体的帧图片。

失败帧列表: {failure_frames}
低置信度帧列表: {low_confidence_frames}

建议：
1. 访问训练数据收集页面查看和下载图片
2. 使用浏览器批量下载功能
3. 或者重新上传视频进行分析
"""
            zip_file.writestr("INFO.txt", info_content)
        
        zip_buffer.seek(0)
        
        # 返回ZIP文件
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=training_data_{job_id}.zip"
            }
        )
        
    except Exception as e:
        print(f"生成训练数据ZIP包失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成ZIP包失败: {str(e)}")


# _generate_failure_frames_html 函数已重构到 html_generator_service

# 重复的 download_training_data_zip 函数已删除
