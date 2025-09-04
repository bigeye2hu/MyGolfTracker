#!/usr/bin/env python3
"""
提取检测失败的帧图片
生成一个网页界面，让用户可以手动下载所有检测失败的帧图片
"""

import sys
import os
sys.path.append('.')

import cv2
import numpy as np
import json
import base64
from datetime import datetime
from detector.yolov8_detector import YOLOv8Detector

def extract_failure_frames_web(video_path):
    """生成一个网页，显示所有检测失败的帧，供用户下载"""
    
    print(f"🔍 分析视频并提取失败帧: {video_path}")
    print("=" * 60)
    
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 无法打开视频: {video_path}")
        return
    
    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📹 视频信息: {width}x{height}, {fps:.1f}fps, {total_frames}帧")
    
    # 初始化检测器
    detector = YOLOv8Detector()
    
    # 收集失败帧
    failure_frames = []
    print("🔍 开始检测...")
    
    for frame_num in range(total_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # 运行检测
        result = detector.detect_single_point(frame, debug=False)
        
        if result is None:  # 检测失败
            # 将帧转换为base64编码的图片
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            failure_frames.append({
                "frame_number": frame_num,
                "timestamp": frame_num / fps,
                "image_data": img_base64,
                "filename": f"failure_frame_{frame_num:03d}.jpg"
            })
        
        # 显示进度
        if frame_num % 20 == 0 or frame_num == total_frames - 1:
            progress = (frame_num + 1) / total_frames * 100
            print(f"   进度: {progress:.1f}% ({frame_num + 1}/{total_frames})")
    
    cap.release()
    
    print(f"\n📊 检测结果:")
    print(f"   - 总帧数: {total_frames}")
    print(f"   - 检测失败: {len(failure_frames)} 帧")
    print(f"   - 失败率: {len(failure_frames)/total_frames*100:.1f}%")
    
    # 生成HTML页面
    html_content = generate_failure_frames_html(failure_frames, os.path.basename(video_path))
    
    # 保存HTML文件
    html_file = "failure_frames_download.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n💾 失败帧下载页面已生成: {html_file}")
    print(f"🌐 请在浏览器中打开: file://{os.path.abspath(html_file)}")
    
    return html_file

def generate_failure_frames_html(failure_frames, video_name):
    """生成包含失败帧的HTML页面"""
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>检测失败帧下载 - {video_name}</title>
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
            border-left: 4px solid #667eea;
        }}
        
        .summary h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .summary p {{
            margin: 5px 0;
            color: #495057;
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
            <p><strong>视频文件:</strong> {video_name}</p>
            <p><strong>失败帧数量:</strong> {len(failure_frames)} 帧</p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>用途:</strong> 这些图片可用于模型训练数据增强，提高杆头检测准确率</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="selectAll()">全选所有帧</button>
            <button class="btn btn-secondary" onclick="clearSelection()">清除选择</button>
            <button class="btn" onclick="downloadSelected()">下载选中帧</button>
        </div>
        
        <div class="select-all">
            <input type="checkbox" id="selectAllCheckbox" onchange="toggleAllSelection()">
            <label for="selectAllCheckbox">全选/取消全选</label>
        </div>
        
        <div class="frames-grid">
"""
    
    # 添加每个失败帧
    for i, frame_data in enumerate(failure_frames):
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
        const failureFrames = """ + json.dumps(failure_frames) + """;
        
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

def main():
    video_path = "/Users/huxiaoran/Desktop/高尔夫测试视频/00001.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 生成失败帧下载页面
    html_file = extract_failure_frames_web(video_path)
    
    print(f"\n🎯 使用说明:")
    print(f"   1. 在浏览器中打开生成的HTML文件")
    print(f"   2. 查看所有检测失败的帧")
    print(f"   3. 选择需要下载的帧（可以全选或单独选择）")
    print(f"   4. 点击'下载选中帧'批量下载")
    print(f"   5. 这些图片可以用于模型训练数据增强")

if __name__ == "__main__":
    main()
