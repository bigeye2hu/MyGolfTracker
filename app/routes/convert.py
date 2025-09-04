"""
独立的视频转换服务
专门处理视频格式转换，与主分析服务分离
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import shutil
import uuid
import threading
import time
import subprocess
from typing import Dict, Any
import cv2

router = APIRouter()

# 转换任务存储
_CONVERSION_JOBS: Dict[str, Dict] = {}

# 服务器资源监控
_SERVER_STATUS = {
    "active_conversions": 0,
    "max_concurrent_conversions": 2,  # 限制并发转换数量
    "server_load": "normal"
}

def _check_video_compatibility(video_path: str) -> Dict[str, Any]:
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

def _check_ffmpeg_available() -> bool:
    """检查FFmpeg是否可用"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def _convert_video_job(job_id: str, input_path: str, output_path: str, quality: str = "medium") -> None:
    """后台视频转换任务"""
    try:
        _CONVERSION_JOBS[job_id]["status"] = "converting"
        _SERVER_STATUS["active_conversions"] += 1
        
        # 检查是否需要转换
        compatibility = _check_video_compatibility(input_path)
        if compatibility.get("compatible", False):
            # 如果已经兼容，直接复制文件
            shutil.copy2(input_path, output_path)
            _CONVERSION_JOBS[job_id]["status"] = "completed"
            _CONVERSION_JOBS[job_id]["message"] = "视频已经是兼容格式，无需转换"
        else:
            # 检查FFmpeg是否可用
            if not _check_ffmpeg_available():
                # 如果FFmpeg不可用，使用OpenCV进行简单转换
                _convert_with_opencv(job_id, input_path, output_path)
            else:
                # 使用FFmpeg进行真正的H.264转换
                _convert_with_ffmpeg(job_id, input_path, output_path, quality)
        
        # 清理输入文件
        try:
            os.remove(input_path)
        except OSError:
            pass
            
    except Exception as e:
        _CONVERSION_JOBS[job_id]["status"] = "error"
        _CONVERSION_JOBS[job_id]["error"] = str(e)
        
        # 清理文件
        try:
            os.remove(input_path)
        except OSError:
            pass
        try:
            os.remove(output_path)
        except OSError:
            pass
    finally:
        _SERVER_STATUS["active_conversions"] = max(0, _SERVER_STATUS["active_conversions"] - 1)

def _convert_with_ffmpeg(job_id: str, input_path: str, output_path: str, quality: str) -> None:
    """使用FFmpeg进行H.264转换"""
    # 质量设置
    quality_settings = {
        "high": ["-crf", "18", "-preset", "slow"],
        "medium": ["-crf", "23", "-preset", "medium"], 
        "low": ["-crf", "28", "-preset", "fast"]
    }
    
    # 构建FFmpeg命令
    cmd = [
        "ffmpeg", "-i", input_path,
        "-c:v", "libx264",  # 使用H.264编码器
        "-c:a", "aac",      # 音频编码器
        "-movflags", "+faststart",  # 优化网络播放
        "-y"  # 覆盖输出文件
    ] + quality_settings.get(quality, quality_settings["medium"])
    
    cmd.append(output_path)
    
    print(f"执行FFmpeg命令: {' '.join(cmd)}")
    
    # 执行转换
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 监控进度（简化版本）
    _CONVERSION_JOBS[job_id]["progress"] = 10
    
    # 等待转换完成
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        _CONVERSION_JOBS[job_id]["status"] = "completed"
        _CONVERSION_JOBS[job_id]["message"] = "视频转换完成（H.264格式）"
        _CONVERSION_JOBS[job_id]["progress"] = 100
        print("FFmpeg转换成功")
    else:
        raise Exception(f"FFmpeg转换失败: {stderr}")

def _convert_with_opencv(job_id: str, input_path: str, output_path: str) -> None:
    """使用OpenCV进行转换（备用方案）"""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise Exception("无法打开输入视频文件")
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 创建视频写入器 - 尝试使用H.264编码器
    fourcc = cv2.VideoWriter_fourcc(*'H264')  # 尝试H.264编码器
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        # 如果H.264不可用，回退到mp4v
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        out.write(frame)
        frame_count += 1
        
        # 更新进度
        progress = int((frame_count / total_frames) * 100)
        _CONVERSION_JOBS[job_id]["progress"] = progress
    
    cap.release()
    out.release()
    
    _CONVERSION_JOBS[job_id]["status"] = "completed"
    _CONVERSION_JOBS[job_id]["message"] = "视频转换完成（OpenCV，可能不是H.264）"
    _CONVERSION_JOBS[job_id]["progress"] = 100

@router.post("/video")
async def convert_video(
    video: UploadFile = File(...),
    quality: str = "medium"
):
    """转换视频格式为H.264 MP4"""
    
    # 检查服务器负载
    if _SERVER_STATUS["active_conversions"] >= _SERVER_STATUS["max_concurrent_conversions"]:
        raise HTTPException(
            status_code=503, 
            detail="服务器转换任务已满，请稍后再试"
        )
    
    # 检查文件类型
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(
            status_code=400,
            detail="请上传视频文件"
        )
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename or "video.mp4")[1]) as tmp:
        shutil.copyfileobj(video.file, tmp)
        input_path = tmp.name
    
    # 生成输出文件路径
    output_filename = f"converted_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    
    # 检查视频兼容性
    compatibility = _check_video_compatibility(input_path)
    
    # 生成任务ID
    job_id = str(uuid.uuid4())
    _CONVERSION_JOBS[job_id] = {
        "status": "queued",
        "progress": 0,
        "input_filename": video.filename,
        "output_filename": output_filename,
        "output_path": output_path,
        "compatibility": compatibility,
        "created_at": time.time()
    }
    
    # 启动转换任务
    thread = threading.Thread(
        target=_convert_video_job, 
        args=(job_id, input_path, output_path, quality),
        daemon=True
    )
    thread.start()
    
    response = {
        "job_id": job_id,
        "status": "queued",
        "message": "视频转换任务已开始",
        "compatibility": compatibility
    }
    
    # 如果不兼容，添加转换说明
    if not compatibility.get("compatible", True):
        response["conversion_info"] = {
            "reason": "检测到不兼容的视频格式",
            "current_codec": compatibility.get("video_info", {}).get("codec", "unknown"),
            "target_codec": "H.264",
            "estimated_time": "1-3分钟"
        }
    else:
        response["conversion_info"] = {
            "reason": "视频已经是兼容格式",
            "action": "将直接复制文件"
        }
    
    return response

@router.get("/status/{job_id}")
async def get_conversion_status(job_id: str):
    """获取转换任务状态"""
    job = _CONVERSION_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="转换任务未找到")
    
    response = {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress", 0),
        "message": job.get("message", "")
    }
    
    if job.get("status") == "completed":
        response["download_url"] = f"/convert/download/{job_id}"
        response["output_filename"] = job.get("output_filename")
    
    if job.get("status") == "error":
        response["error"] = job.get("error")
    
    return response

@router.get("/download/{job_id}")
async def download_converted_video(job_id: str):
    """下载转换后的视频文件"""
    job = _CONVERSION_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="转换任务未找到")
    
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="转换任务尚未完成")
    
    output_path = job.get("output_path")
    output_filename = job.get("output_filename")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="转换后的文件不存在")
    
    # 返回文件下载响应
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type='video/mp4',
        headers={"Content-Disposition": f"attachment; filename={output_filename}"}
    )

@router.get("/server-status")
async def get_server_status():
    """获取转换服务器状态"""
    return {
        "active_conversions": _SERVER_STATUS["active_conversions"],
        "max_concurrent_conversions": _SERVER_STATUS["max_concurrent_conversions"],
        "server_load": _SERVER_STATUS["server_load"],
        "available_slots": _SERVER_STATUS["max_concurrent_conversions"] - _SERVER_STATUS["active_conversions"],
        "queue_length": len([job for job in _CONVERSION_JOBS.values() if job.get("status") == "queued"])
    }

@router.get("/supported-formats")
async def get_supported_formats():
    """返回支持的视频格式信息"""
    return {
        "title": "视频转换服务 - 支持的格式",
        "input_formats": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
        "output_format": ".mp4",
        "output_codec": "H.264",
        "quality_options": ["high", "medium", "low"],
        "max_file_size": "100MB",
        "max_duration": "10分钟"
    }

@router.get("/test-page")
async def get_conversion_test_page():
    """返回转换服务测试页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GolfTracker 视频转换服务</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 {
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 50px;
            text-align: center;
            margin: 30px 0;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .upload-area::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        .upload-area:hover::before {
            left: 100%;
        }
        .upload-area.dragover {
            border-color: #764ba2;
            background: linear-gradient(135deg, rgba(118, 75, 162, 0.2), rgba(102, 126, 234, 0.2));
            transform: scale(1.02);
        }
        input[type="file"] {
            margin: 15px 0;
            font-size: 16px;
            padding: 10px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            background: white;
            transition: border-color 0.3s ease;
        }
        input[type="file"]:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin: 10px 8px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }
        button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        button:hover::before {
            left: 100%;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            background: linear-gradient(135deg, #bdc3c7, #95a5a6);
            cursor: not-allowed;
            transform: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .status {
            margin: 25px 0;
            padding: 20px;
            border-radius: 15px;
            display: none;
            font-size: 16px;
            font-weight: 500;
            backdrop-filter: blur(10px);
            border: 2px solid;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .status.success {
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.2), rgba(25, 135, 84, 0.2));
            border-color: #28a745;
            color: #155724;
        }
        .status.error {
            background: linear-gradient(135deg, rgba(220, 53, 69, 0.2), rgba(200, 35, 51, 0.2));
            border-color: #dc3545;
            color: #721c24;
        }
        .status.info {
            background: linear-gradient(135deg, rgba(13, 202, 240, 0.2), rgba(6, 182, 212, 0.2));
            border-color: #0dcaf0;
            color: #0c5460;
        }
        .progress-bar {
            width: 100%;
            height: 25px;
            background: linear-gradient(135deg, #e9ecef, #f8f9fa);
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid #e0e0e0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #28a745, #20c997);
            width: 0%;
            transition: width 0.5s ease;
            border-radius: 13px;
            position: relative;
            overflow: hidden;
        }
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background-image: linear-gradient(
                -45deg,
                rgba(255, 255, 255, .2) 25%,
                transparent 25%,
                transparent 50%,
                rgba(255, 255, 255, .2) 50%,
                rgba(255, 255, 255, .2) 75%,
                transparent 75%,
                transparent
            );
            background-size: 20px 20px;
            animation: move 1s linear infinite;
        }
        @keyframes move {
            0% { background-position: 0 0; }
            100% { background-position: 20px 20px; }
        }
        .server-status {
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(25, 135, 84, 0.1));
            border: 2px solid #28a745;
            border-radius: 15px;
            padding: 20px;
            margin: 25px 0;
            backdrop-filter: blur(10px);
        }
        .server-status h3 {
            color: #155724;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .format-info {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 152, 0, 0.1));
            border: 2px solid #ffc107;
            border-radius: 15px;
            padding: 20px;
            margin: 25px 0;
            backdrop-filter: blur(10px);
        }
        .format-info h3 {
            color: #856404;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .format-info p {
            font-size: 16px;
            line-height: 1.6;
            margin: 8px 0;
        }
        .format-info strong {
            color: #495057;
            font-weight: 600;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 20px;
            }
            h1 {
                font-size: 2em;
            }
            .upload-area {
                padding: 30px 20px;
            }
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2, #667eea);
        }
        
        /* 选择框样式 */
        select {
            transition: all 0.3s ease;
        }
        select:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* 文件输入样式 */
        input[type="file"] {
            transition: all 0.3s ease;
        }
        input[type="file"]:hover {
            border-color: #667eea;
            transform: translateY(-1px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 GolfTracker 视频转换服务</h1>
        
        <div class="server-status">
            <h3>📊 服务器状态</h3>
            <div id="serverStatus">正在检查服务器状态...</div>
        </div>
        
        <div class="format-info">
            <h3>📋 支持的格式</h3>
            <p><strong>输入格式：</strong>MP4, MOV, AVI, MKV, WMV, FLV, WEBM</p>
            <p><strong>输出格式：</strong>H.264编码的MP4文件</p>
            <p><strong>最大文件大小：</strong>100MB</p>
            <p><strong>最大时长：</strong>10分钟</p>
        </div>
        
        <div class="upload-area" id="uploadArea">
            <h3 style="font-size: 1.5em; margin-bottom: 20px; color: #495057; font-weight: 600;">📤 上传视频文件</h3>
            <p style="font-size: 18px; color: #6c757d; margin-bottom: 25px; font-weight: 500;">拖拽文件到此处或点击选择文件</p>
            <input type="file" id="videoFile" accept="video/*" />
            <br>
            <label for="quality" style="font-size: 16px; font-weight: 600; color: #495057; margin-top: 20px; display: inline-block;">转换质量：</label>
            <select id="quality" style="font-size: 16px; padding: 8px 15px; border-radius: 8px; border: 2px solid #e0e0e0; background: white; margin-left: 10px;">
                <option value="medium">中等质量（推荐）</option>
                <option value="high">高质量</option>
                <option value="low">低质量</option>
            </select>
            <br><br>
            <button id="convertBtn" onclick="startConversion()" style="font-size: 18px; padding: 18px 35px;">🚀 开始转换</button>
        </div>
        
        <div class="status" id="statusDiv">
            <div id="statusMessage"></div>
            <div class="progress-bar" id="progressBar" style="display: none;">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>
        
        <div id="downloadSection" style="display: none; text-align: center; padding: 30px; background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(25, 135, 84, 0.1)); border-radius: 15px; border: 2px solid #28a745; margin: 25px 0;">
            <h3 style="font-size: 1.8em; color: #155724; margin-bottom: 20px; font-weight: 700;">✅ 转换完成</h3>
            <p style="font-size: 16px; color: #495057; margin-bottom: 25px;">您的视频已成功转换为H.264格式，现在可以下载了！</p>
            <button onclick="downloadVideo()" style="font-size: 18px; padding: 18px 35px; background: linear-gradient(135deg, #28a745, #20c997);">📥 下载转换后的视频</button>
        </div>
    </div>

    <script>
        let currentJobId = null;
        let pollInterval = null;
        
        // 检查服务器状态
        async function checkServerStatus() {
            try {
                const response = await fetch('/convert/server-status');
                const status = await response.json();
                
                document.getElementById('serverStatus').innerHTML = `
                    <p>活跃转换任务: ${status.active_conversions}/${status.max_concurrent_conversions}</p>
                    <p>可用槽位: ${status.available_slots}</p>
                    <p>队列长度: ${status.queue_length}</p>
                    <p>服务器负载: ${status.server_load}</p>
                `;
            } catch (error) {
                document.getElementById('serverStatus').innerHTML = '<p style="color: red;">无法连接到服务器</p>';
            }
        }
        
        // 开始转换
        async function startConversion() {
            const fileInput = document.getElementById('videoFile');
            const quality = document.getElementById('quality').value;
            
            if (!fileInput.files[0]) {
                showStatus('请选择视频文件', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('video', fileInput.files[0]);
            formData.append('quality', quality);
            
            try {
                showStatus('正在上传视频...', 'info');
                document.getElementById('convertBtn').disabled = true;
                
                const response = await fetch('/convert/video', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    currentJobId = result.job_id;
                    showStatus('转换任务已开始，正在处理...', 'info');
                    document.getElementById('progressBar').style.display = 'block';
                    startPolling();
                } else {
                    showStatus(`转换失败: ${result.detail}`, 'error');
                    document.getElementById('convertBtn').disabled = false;
                }
            } catch (error) {
                showStatus(`上传失败: ${error.message}`, 'error');
                document.getElementById('convertBtn').disabled = false;
            }
        }
        
        // 开始轮询转换状态
        function startPolling() {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/convert/status/${currentJobId}`);
                    const status = await response.json();
                    
                    updateProgress(status.progress);
                    showStatus(status.message || `转换中... ${status.progress}%`, 'info');
                    
                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        showStatus('转换完成！', 'success');
                        document.getElementById('downloadSection').style.display = 'block';
                        document.getElementById('progressBar').style.display = 'none';
                    } else if (status.status === 'error') {
                        clearInterval(pollInterval);
                        showStatus(`转换失败: ${status.error}`, 'error');
                        document.getElementById('convertBtn').disabled = false;
                    }
                } catch (error) {
                    clearInterval(pollInterval);
                    showStatus(`状态检查失败: ${error.message}`, 'error');
                    document.getElementById('convertBtn').disabled = false;
                }
            }, 2000);
        }
        
        // 更新进度条
        function updateProgress(progress) {
            document.getElementById('progressFill').style.width = progress + '%';
        }
        
        // 显示状态信息
        function showStatus(message, type) {
            const statusDiv = document.getElementById('statusDiv');
            const statusMessage = document.getElementById('statusMessage');
            
            statusDiv.className = `status ${type}`;
            statusMessage.textContent = message;
            statusDiv.style.display = 'block';
        }
        
        // 下载转换后的视频
        function downloadVideo() {
            if (currentJobId) {
                window.open(`/convert/download/${currentJobId}`, '_blank');
            }
        }
        
        // 拖拽上传
        const uploadArea = document.getElementById('uploadArea');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('videoFile').files = files;
            }
        });
        
        // 页面加载时检查服务器状态
        checkServerStatus();
        setInterval(checkServerStatus, 10000); // 每10秒检查一次
    </script>
</body>
</html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
