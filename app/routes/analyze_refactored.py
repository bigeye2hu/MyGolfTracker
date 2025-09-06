"""
重构后的分析路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import List, Dict, Any
import uuid
import os
import shutil
import io

# 导入服务层
from app.services.video_service import video_analysis_service
from app.services.training_service import training_data_service
from app.services.html_generator import html_generator_service
from app.utils.file_utils import check_video_compatibility, create_temp_file, cleanup_temp_file

router = APIRouter()

# 服务器资源监控
_SERVER_STATUS = {
    "active_conversions": 0,
    "max_concurrent_conversions": 3,
    "server_load": "normal"
}


@router.post("/analyze")
async def analyze(
    video: UploadFile = File(...),
    resolution: str = Form("480"),
    confidence: str = Form("0.01"),
    iou: str = Form("0.7"),
    max_det: str = Form("10"),
    optimization_strategy: str = Form("original")
):
    """分析上传的视频文件，返回YOLOv8检测结果"""
    try:
        # 检查文件类型
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="请上传视频文件")
        
        # 创建临时文件
        temp_file_path = create_temp_file()
        
        try:
            # 保存上传的文件
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            
            # 检查视频兼容性
            compatibility = check_video_compatibility(temp_file_path)
            if not compatibility["compatible"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"视频文件不兼容: {compatibility['error']}"
                )
            
            # 生成任务ID
            job_id = str(uuid.uuid4())
            
            # 启动分析任务
            video_analysis_service.start_analysis_job(
                job_id, temp_file_path, resolution, confidence, iou, max_det, optimization_strategy
            )
            
            return {
                "job_id": job_id,
                "status": "queued",
                "message": "分析任务已启动",
                "compatibility": compatibility
            }
            
        finally:
            # 清理临时文件
            cleanup_temp_file(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/video/status")
async def analyze_video_status(job_id: str):
    """获取视频分析状态"""
    try:
        status = video_analysis_service.get_job_status(job_id)
        
        if status["status"] == "done":
            # 生成训练数据页面
            result = status["result"]
            failure_frames = [i for i, phase in enumerate(result.get("swing_phases", [])) 
                            if phase == "failure"]
            low_confidence_frames = [i for i, conf in enumerate(result.get("club_head_trajectory", [])) 
                                   if conf[2] < 0.5]  # 假设第三个元素是置信度
            
            training_data_url = training_data_service.generate_training_data_page(
                job_id, "", failure_frames, low_confidence_frames, 0.5
            )
            
            # 添加训练数据URL到结果中
            result["training_data_url"] = training_data_url
            
            return {
                "status": "done",
                "result": result,
                "job_id": job_id
            }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/visualize/{result_id}")
async def get_visualization_page(result_id: str):
    """返回分析结果可视化页面"""
    try:
        # 从分析结果中获取数据
        analysis_data = video_analysis_service.get_analysis_result(result_id)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        # 生成可视化页面
        html_content = html_generator_service.generate_visualization_page(result_id, analysis_data)
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成可视化页面失败: {str(e)}")


@router.get("/strategies")
async def get_strategies():
    """获取所有可用策略"""
    try:
        from analyzer.strategy_manager import get_strategy_manager
        strategy_manager = get_strategy_manager()
        strategies = strategy_manager.get_all_strategies()
        return {"strategies": strategies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.get("/strategies/{category}")
async def get_strategies_by_category(category: str):
    """按类别获取策略"""
    try:
        from analyzer.strategy_manager import get_strategy_manager
        strategy_manager = get_strategy_manager()
        strategies = strategy_manager.get_strategies_by_category(category)
        return {"strategies": strategies, "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.get("/strategy-test")
async def get_strategy_test_page():
    """返回策略管理测试页面"""
    try:
        html_content = html_generator_service.generate_strategy_test_page()
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成策略测试页面失败: {str(e)}")


@router.get("/server-test")
async def get_server_test_page():
    """返回服务器端测试页面"""
    try:
        html_content = html_generator_service.generate_server_test_page()
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成服务器测试页面失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """返回支持的视频格式信息"""
    return {
        "supported_formats": [
            {"extension": ".mp4", "description": "MP4视频文件", "codec": "H.264/H.265"},
            {"extension": ".avi", "description": "AVI视频文件", "codec": "多种编解码器"},
            {"extension": ".mov", "description": "QuickTime视频文件", "codec": "H.264/ProRes"},
            {"extension": ".mkv", "description": "Matroska视频文件", "codec": "多种编解码器"},
            {"extension": ".wmv", "description": "Windows Media视频文件", "codec": "WMV"},
            {"extension": ".flv", "description": "Flash视频文件", "codec": "H.264/VP6"},
            {"extension": ".webm", "description": "WebM视频文件", "codec": "VP8/VP9"}
        ],
        "recommended_formats": [".mp4", ".mov"],
        "max_file_size": "100MB",
        "notes": [
            "推荐使用MP4格式以获得最佳兼容性",
            "文件大小建议不超过100MB",
            "支持常见的高清和标清视频"
        ]
    }


@router.get("/conversion-guide")
async def get_conversion_guide():
    """返回视频转换指导信息"""
    return {
        "conversion_tools": [
            {
                "name": "FFmpeg",
                "description": "强大的命令行视频处理工具",
                "download_url": "https://ffmpeg.org/download.html",
                "commands": [
                    "ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4",
                    "ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac output.mp4"
                ]
            },
            {
                "name": "HandBrake",
                "description": "图形化视频转换工具",
                "download_url": "https://handbrake.fr/downloads.php",
                "features": ["图形界面", "预设配置", "批量转换"]
            },
            {
                "name": "VLC Media Player",
                "description": "免费的多媒体播放器，支持格式转换",
                "download_url": "https://www.videolan.org/vlc/",
                "features": ["简单易用", "支持多种格式", "免费"]
            }
        ],
        "conversion_tips": [
            "使用H.264编码器以获得最佳兼容性",
            "设置合适的比特率以平衡文件大小和质量",
            "保持原始帧率以避免播放问题",
            "选择AAC音频编码器"
        ],
        "quality_settings": {
            "high_quality": "CRF 18-23",
            "medium_quality": "CRF 24-28",
            "low_quality": "CRF 29-35"
        }
    }


@router.get("/training-data/zip/{job_id}")
async def download_training_data_zip(job_id: str):
    """下载训练数据ZIP包"""
    try:
        # 生成ZIP包
        zip_data = training_data_service.generate_training_data_zip(job_id)
        
        # 返回ZIP文件
        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=training_data_{job_id}.zip"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成ZIP包失败: {str(e)}")


@router.post("/video")
async def analyze_video_test(
    video: UploadFile = File(...),
    resolution: str = Form("480"),
    confidence: str = Form("0.01"),
    iou: str = Form("0.7"),
    max_det: str = Form("10"),
    optimization_strategy: str = Form("original")
):
    """测试视频分析接口"""
    try:
        # 检查文件类型
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="请上传视频文件")
        
        # 创建临时文件
        temp_file_path = create_temp_file()
        
        try:
            # 保存上传的文件
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            
            # 检查视频兼容性
            compatibility = check_video_compatibility(temp_file_path)
            if not compatibility["compatible"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"视频文件不兼容: {compatibility['error']}"
                )
            
            # 生成任务ID
            job_id = str(uuid.uuid4())
            
            # 启动分析任务
            video_analysis_service.start_analysis_job(
                job_id, temp_file_path, resolution, confidence, iou, max_det, optimization_strategy
            )
            
            return {
                "job_id": job_id,
                "status": "queued",
                "message": "分析任务已启动",
                "compatibility": compatibility,
                "test_mode": True
            }
            
        finally:
            # 清理临时文件
            cleanup_temp_file(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试分析失败: {str(e)}")
