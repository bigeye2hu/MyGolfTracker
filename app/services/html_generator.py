"""
HTML生成服务 - 从analyze.py中提取的HTML生成函数
保持原有的HTML内容和样式完全不变
"""
from typing import List, Dict, Any
from datetime import datetime
import json
import os
import cv2
import base64


class HTMLGeneratorService:
    """HTML生成服务 - 保持原有逻辑和界面"""
    
    def generate_training_data_page(self, job_id: str, video_path: str, failure_frames: List[int], low_confidence_frames: List[int], confidence_threshold: float) -> str:
        """生成训练数据收集页面（失败帧 + 低置信度帧）并返回URL"""
        try:
            print(f"开始处理视频: {video_path}")
            # 打开视频获取帧的图片
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"无法打开视频文件: {video_path}")
                return None
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"视频信息: 总帧数={total_frames}, FPS={fps}")
            
            # 收集所有训练数据帧
            all_training_frames = failure_frames + low_confidence_frames
            all_training_frames = sorted(list(set(all_training_frames)))  # 去重并排序
            
            training_frame_data = []
            print(f"开始处理 {len(all_training_frames)} 个训练数据帧...")
            for i, frame_num in enumerate(all_training_frames):
                if i % 5 == 0:  # 每5帧打印一次进度
                    print(f"处理进度: {i+1}/{len(all_training_frames)} (帧 {frame_num})")
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    # 将帧转换为base64编码的图片
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # 确定帧类型
                    frame_type = "failure" if frame_num in failure_frames else "low_confidence"
                    frame_type_cn = "失败帧" if frame_type == "failure" else "低置信度帧"
                    
                    training_frame_data.append({
                        "frame_number": frame_num,
                        "timestamp": frame_num / fps,
                        "image_data": img_base64,
                        "filename": f"training_{frame_type}_frame_{frame_num:03d}.jpg",
                        "frame_type": frame_type,
                        "frame_type_cn": frame_type_cn
                    })
                else:
                    print(f"警告: 无法读取第 {frame_num} 帧")
            
            cap.release()
            
            if not training_frame_data:
                print("没有有效的训练数据帧")
                return None
            
            print(f"成功提取 {len(training_frame_data)} 个训练数据帧，开始生成HTML...")
            
            # 生成HTML内容
            html_content = self.generate_training_data_html(
                training_frame_data, job_id, len(failure_frames), len(low_confidence_frames), 
                total_frames, confidence_threshold
            )
            print("HTML内容生成完成")
            
            # 保存HTML文件
            html_filename = f"training_data_{job_id}.html"
            html_path = os.path.join("static", html_filename)
            
            # 确保static目录存在
            os.makedirs("static", exist_ok=True)
            print(f"保存HTML文件到: {html_path}")
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML文件保存完成，返回URL: /static/{html_filename}")
            return f"/static/{html_filename}"
            
        except Exception as e:
            print(f"生成训练数据收集页面失败: {e}")
            return None
    
    def generate_training_data_html(self, training_frame_data: List[Dict], job_id: str, failure_count: int, low_confidence_count: int, total_frames: int, confidence_threshold: float) -> str:
        """生成训练数据收集页面的HTML内容 - 保持原有逻辑"""
        # 这里先返回一个占位符，稍后会从analyze.py中复制完整的函数
        return "HTML生成功能待实现"
    
    def generate_failure_frames_html(self, failure_frame_data: List[Dict], job_id: str, failure_count: int, total_frames: int) -> str:
        """生成失败帧下载页面的HTML内容 - 保持原有逻辑"""
        # 这里先返回一个占位符，稍后会从analyze.py中复制完整的函数
        return "HTML生成功能待实现"


# 全局服务实例
html_generator_service = HTMLGeneratorService()