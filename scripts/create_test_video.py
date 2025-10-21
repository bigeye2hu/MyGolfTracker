#!/usr/bin/env python3
"""
创建测试视频脚本 - 生成一个简单的测试视频用于性能测试
"""
import cv2
import numpy as np
import os
import sys

def create_test_video(output_path: str, duration: int = 10, fps: int = 30, width: int = 640, height: int = 480):
    """
    创建一个简单的测试视频
    
    Args:
        output_path: 输出视频路径
        duration: 视频时长（秒）
        fps: 帧率
        width: 视频宽度
        height: 视频高度
    """
    print(f"🎬 创建测试视频: {output_path}")
    print(f"   时长: {duration}秒")
    print(f"   帧率: {fps}fps")
    print(f"   分辨率: {width}x{height}")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # 创建黑色背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加一些简单的图形元素
        # 绘制一个移动的白色圆圈（模拟球）
        ball_x = int((frame_num / total_frames) * (width - 50) + 25)
        ball_y = height // 2
        cv2.circle(frame, (ball_x, ball_y), 20, (255, 255, 255), -1)
        
        # 绘制一个移动的矩形（模拟球杆）
        club_x = ball_x - 100
        club_y = ball_y - 10
        cv2.rectangle(frame, (club_x, club_y), (club_x + 80, club_y + 20), (200, 200, 200), -1)
        
        # 添加帧号文本
        cv2.putText(frame, f"Frame: {frame_num}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 添加时间戳
        time_sec = frame_num / fps
        cv2.putText(frame, f"Time: {time_sec:.1f}s", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 写入帧
        out.write(frame)
        
        # 显示进度
        if frame_num % (total_frames // 10) == 0:
            progress = (frame_num / total_frames) * 100
            print(f"   进度: {progress:.0f}%")
    
    # 释放资源
    out.release()
    
    print(f"✅ 测试视频创建完成: {output_path}")
    
    # 检查文件大小
    file_size = os.path.getsize(output_path)
    print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python create_test_video.py <输出路径> [时长(秒)] [帧率] [宽度] [高度]")
        print("示例: python create_test_video.py test_video.mp4 15 30 640 480")
        sys.exit(1)
    
    output_path = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 640
    height = int(sys.argv[5]) if len(sys.argv) > 5 else 480
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    create_test_video(output_path, duration, fps, width, height)

if __name__ == "__main__":
    main()

