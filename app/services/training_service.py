"""
训练数据服务
"""
import os
import tempfile
import shutil
import json
import base64
import zipfile
import io
from typing import List, Dict, Any
from datetime import datetime

import cv2
import numpy as np

from analyzer.ffmpeg import iter_video_frames


class TrainingDataService:
    """训练数据服务"""
    
    def __init__(self):
        self.training_data_cache: Dict[str, Dict] = {}
    
    def generate_training_data_page(self, job_id: str, video_path: str, 
                                  failure_frames: List[int], low_confidence_frames: List[int], 
                                  confidence_threshold: float) -> str:
        """生成训练数据收集页面URL"""
        try:
            # 生成训练数据帧
            training_frame_data = self._extract_training_frames(
                video_path, failure_frames, low_confidence_frames, confidence_threshold
            )
            
            # 生成HTML内容
            html_content = self._generate_training_data_html(
                training_frame_data, job_id, len(failure_frames), 
                len(low_confidence_frames), len(training_frame_data), confidence_threshold
            )
            
            # 保存HTML文件
            html_filename = f"training_data_{job_id}.html"
            html_path = os.path.join("static", html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 生成URL
            training_data_url = f"/static/{html_filename}"
            
            # 缓存数据
            self.training_data_cache[job_id] = {
                "training_data_url": training_data_url,
                "training_frame_data": training_frame_data,
                "failure_count": len(failure_frames),
                "low_confidence_count": len(low_confidence_frames),
                "total_frames": len(training_frame_data),
                "confidence_threshold": confidence_threshold
            }
            
            return training_data_url
            
        except Exception as e:
            print(f"生成训练数据页面失败: {e}")
            raise
    
    def _extract_training_frames(self, video_path: str, failure_frames: List[int], 
                               low_confidence_frames: List[int], confidence_threshold: float) -> List[Dict]:
        """提取训练数据帧"""
        training_frames = []
        
        # 处理失败帧
        for frame_num in failure_frames:
            frame_data = self._extract_frame_data(video_path, frame_num, "failure")
            if frame_data:
                training_frames.append(frame_data)
        
        # 处理低置信度帧
        for frame_num in low_confidence_frames:
            frame_data = self._extract_frame_data(video_path, frame_num, "low_confidence")
            if frame_data:
                training_frames.append(frame_data)
        
        return training_frames
    
    def _extract_frame_data(self, video_path: str, frame_number: int, frame_type: str) -> Dict:
        """提取单帧数据"""
        try:
            # 从视频中提取指定帧
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # 编码为base64
            _, buffer = cv2.imencode('.jpg', frame)
            image_data = base64.b64encode(buffer).decode('utf-8')
            
            # 计算时间戳
            fps = cap.get(cv2.CAP_PROP_FPS) if cap else 30
            timestamp = frame_number / fps
            
            return {
                "frame_number": frame_number,
                "timestamp": timestamp,
                "frame_type": frame_type,
                "frame_type_cn": "失败帧" if frame_type == "failure" else "低置信度帧",
                "image_data": image_data,
                "filename": f"frame_{frame_number:04d}.jpg"
            }
            
        except Exception as e:
            print(f"提取帧 {frame_number} 失败: {e}")
            return None
    
    def _generate_training_data_html(self, training_frame_data: List[Dict], job_id: str, 
                                   failure_count: int, low_confidence_count: int, 
                                   total_frames: int, confidence_threshold: float) -> str:
        """生成训练数据HTML内容"""
        total_training_frames = len(training_frame_data)
        failure_rate = (failure_count / total_frames) * 100
        low_confidence_rate = (low_confidence_count / total_frames) * 100
        total_training_rate = (total_training_frames / total_frames) * 100
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>训练数据收集 - Job {job_id[:8]}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-success {{
            background: #28a745;
        }}
        
        .btn-primary {{
            background: #007bff;
        }}
        
        .filter-controls {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        .filter-controls label {{
            display: inline-block;
            margin-right: 20px;
            cursor: pointer;
        }}
        
        .filter-controls input[type="checkbox"] {{
            margin-right: 8px;
        }}
        
        .frames-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .frame-item {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .frame-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .frame-item.selected {{
            border: 3px solid #667eea;
        }}
        
        .frame-item.failure {{
            border-left: 5px solid #dc3545;
        }}
        
        .frame-item.low_confidence {{
            border-left: 5px solid #ffc107;
        }}
        
        .frame-image {{
            width: 100%;
            height: 200px;
            object-fit: cover;
        }}
        
        .frame-info {{
            padding: 15px;
        }}
        
        .frame-type {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .frame-type.failure {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .frame-type.low_confidence {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .frame-info h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        
        .frame-info p {{
            margin: 5px 0;
            color: #666;
            font-size: 0.9em;
        }}
        
        .download-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .download-btn:hover {{
            background: #218838;
        }}
        
        .select-all {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        
        .select-all input[type="checkbox"] {{
            margin-right: 10px;
        }}
        
        .select-all label {{
            font-weight: bold;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 训练数据收集</h1>
        <p>收集失败帧和低置信度帧，用于模型训练数据增强</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{total_training_frames}</div>
            <div class="stat-label">总训练帧数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{failure_count}</div>
            <div class="stat-label">失败帧</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{low_confidence_count}</div>
            <div class="stat-label">低置信度帧</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{confidence_threshold}</div>
            <div class="stat-label">置信度阈值</div>
        </div>
    </div>
    
    <div class="info">
        <p><strong>任务ID:</strong> {job_id}</p>
        <p><strong>置信度阈值:</strong> {confidence_threshold}</p>
        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>用途:</strong> 这些图片可用于模型训练数据增强，提高杆头检测准确率</p>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="selectAll()">全选所有帧</button>
        <button class="btn btn-secondary" onclick="clearSelection()">清除选择</button>
        <button class="btn btn-success" onclick="downloadSelected()">下载选中帧</button>
        <button class="btn" onclick="downloadAll()">下载全部帧</button>
        <button class="btn btn-primary" onclick="downloadZip()">📦 下载ZIP包</button>
        <a href="/analyze/server-test" class="btn btn-secondary">返回主页面</a>
    </div>
    
    <div class="filter-controls">
        <label>
            <input type="checkbox" id="filterFailure" checked onchange="filterFrames()">
            显示失败帧
        </label>
        <label>
            <input type="checkbox" id="filterLowConfidence" checked onchange="filterFrames()">
            显示低置信度帧
        </label>
    </div>
    
    <div class="select-all">
        <input type="checkbox" id="selectAllCheckbox" onchange="toggleAllSelection()">
        <label for="selectAllCheckbox">全选/取消全选</label>
    </div>
    
    <div class="frames-grid" id="framesGrid">
"""
        
        # 添加每个训练数据帧
        for i, frame_data in enumerate(training_frame_data):
            html += f"""
            <div class="frame-item {frame_data['frame_type']}" data-frame="{frame_data['frame_number']}" data-type="{frame_data['frame_type']}">
                <img src="data:image/jpeg;base64,{frame_data['image_data']}" 
                     alt="Frame {frame_data['frame_number']}" 
                     class="frame-image">
                <div class="frame-info">
                    <div class="frame-type {frame_data['frame_type']}">{frame_data['frame_type_cn']}</div>
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
        const trainingFrames = """ + json.dumps(training_frame_data) + """;
        
        function selectAll() {
            const visibleItems = document.querySelectorAll('.frame-item:not([style*="display: none"])');
            visibleItems.forEach(item => {
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
        
        function filterFrames() {
            const showFailure = document.getElementById('filterFailure').checked;
            const showLowConfidence = document.getElementById('filterLowConfidence').checked;
            const items = document.querySelectorAll('.frame-item');
            
            items.forEach(item => {
                const frameType = item.dataset.type;
                if ((frameType === 'failure' && showFailure) || 
                    (frameType === 'low_confidence' && showLowConfidence)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // 更新全选状态
            updateSelectAllCheckbox();
        }
        
        function updateSelectAllCheckbox() {
            const visibleItems = document.querySelectorAll('.frame-item:not([style*="display: none"])');
            const selectedItems = document.querySelectorAll('.frame-item.selected:not([style*="display: none"])');
            const checkbox = document.getElementById('selectAllCheckbox');
            
            if (visibleItems.length === 0) {
                checkbox.checked = false;
                checkbox.indeterminate = false;
            } else if (selectedItems.length === visibleItems.length) {
                checkbox.checked = true;
                checkbox.indeterminate = false;
            } else if (selectedItems.length > 0) {
                checkbox.checked = false;
                checkbox.indeterminate = true;
            } else {
                checkbox.checked = false;
                checkbox.indeterminate = false;
            }
        }
        
        function downloadSingleFrame(index) {
            const frame = trainingFrames[index];
            downloadFrame(frame);
        }
        
        function downloadSelected() {
            const selectedItems = document.querySelectorAll('.frame-item.selected:not([style*="display: none"])');
            if (selectedItems.length === 0) {
                alert('请先选择要下载的帧！');
                return;
            }
            
            selectedItems.forEach(item => {
                const frameNumber = parseInt(item.dataset.frame);
                const frame = trainingFrames.find(f => f.frame_number === frameNumber);
                if (frame) {
                    downloadFrame(frame);
                }
            });
        }
        
        function downloadAll() {
            const visibleItems = document.querySelectorAll('.frame-item:not([style*="display: none"])');
            if (visibleItems.length === 0) {
                alert('没有可下载的帧！');
                return;
            }
            
            visibleItems.forEach(item => {
                const frameNumber = parseInt(item.dataset.frame);
                const frame = trainingFrames.find(f => f.frame_number === frameNumber);
                if (frame) {
                    downloadFrame(frame);
                }
            });
        }
        
        function downloadZip() {
            const jobId = '{job_id}';
            const zipUrl = `/analyze/training-data/zip/${jobId}`;
            
            // 创建下载链接
            const link = document.createElement('a');
            link.href = zipUrl;
            link.download = `training_data_${jobId}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
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
        
        // 添加点击选择功能
        document.addEventListener('DOMContentLoaded', function() {
            const frameItems = document.querySelectorAll('.frame-item');
            frameItems.forEach(item => {
                item.addEventListener('click', function(e) {
                    if (e.target.tagName !== 'BUTTON') {
                        this.classList.toggle('selected');
                        updateSelectAllCheckbox();
                    }
                });
            });
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def generate_training_data_zip(self, job_id: str) -> bytes:
        """生成训练数据ZIP包"""
        if job_id not in self.training_data_cache:
            raise ValueError("任务不存在")
        
        cache_data = self.training_data_cache[job_id]
        training_frame_data = cache_data["training_frame_data"]
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 添加README文件
            readme_content = f"""# 训练数据收集包

## 任务信息
- 任务ID: {job_id}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 总帧数: {cache_data['total_frames']}
- 失败帧数: {cache_data['failure_count']}
- 低置信度帧数: {cache_data['low_confidence_count']}
- 置信度阈值: {cache_data['confidence_threshold']}

## 文件说明
- failure_frames/: 失败帧图片
- low_confidence_frames/: 低置信度帧图片
- info.json: 帧信息元数据

## 用途
这些图片可用于模型训练数据增强，提高杆头检测准确率。

## 注意事项
- 图片格式: JPEG
- 命名规则: frame_XXXX.jpg (XXXX为帧号)
- 建议用于数据增强和模型微调
"""
            
            zip_file.writestr("README.md", readme_content)
            
            # 添加帧信息JSON
            frame_info = {
                "job_id": job_id,
                "total_frames": cache_data['total_frames'],
                "failure_count": cache_data['failure_count'],
                "low_confidence_count": cache_data['low_confidence_count'],
                "confidence_threshold": cache_data['confidence_threshold'],
                "frames": training_frame_data
            }
            
            zip_file.writestr("info.json", json.dumps(frame_info, indent=2, ensure_ascii=False))
            
            # 添加图片文件
            for frame_data in training_frame_data:
                frame_type = frame_data['frame_type']
                filename = frame_data['filename']
                image_data = base64.b64decode(frame_data['image_data'])
                
                zip_file.writestr(f"{frame_type}_frames/{filename}", image_data)
            
            # 添加说明文件
            info_content = f"""注意：由于视频文件已被处理，无法直接生成ZIP包中的图片文件。
请使用网页界面下载具体的图片文件。

任务ID: {job_id}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            zip_file.writestr("info.txt", info_content)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()


# 全局服务实例
training_data_service = TrainingDataService()
