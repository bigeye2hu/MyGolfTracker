#!/usr/bin/env python3
"""
生成检测失败报告
记录所有返回None的位置数据，用于后续模型训练参考
"""

import sys
import os
sys.path.append('.')

import cv2
import numpy as np
import json
from datetime import datetime
from detector.yolov8_detector import YOLOv8Detector

def analyze_video_detection_failures(video_path, output_file="detection_failure_report.json"):
    """分析视频中所有检测失败的位置"""
    print(f"🔍 分析视频检测失败情况: {video_path}")
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
    duration = total_frames / fps
    
    print(f"📹 视频信息:")
    print(f"   - 总帧数: {total_frames}")
    print(f"   - 帧率: {fps:.1f} fps")
    print(f"   - 尺寸: {width}x{height}")
    print(f"   - 时长: {duration:.1f}秒")
    print()
    
    # 初始化检测器
    detector = YOLOv8Detector()
    
    # 统计变量
    detection_results = []
    failure_frames = []
    success_frames = []
    total_detections = 0
    successful_detections = 0
    
    print("🔍 开始逐帧检测...")
    
    # 逐帧检测
    for frame_num in range(total_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if not ret:
            print(f"❌ 无法读取第 {frame_num} 帧")
            continue
        
        # 运行检测
        result = detector.detect_single_point(frame, debug=False)
        
        # 记录结果
        frame_info = {
            "frame_number": frame_num,
            "timestamp": frame_num / fps,
            "detected": result is not None
        }
        
        if result:
            cx, cy, conf = result
            norm_x = cx / width
            norm_y = cy / height
            
            frame_info.update({
                "center_x": float(cx),
                "center_y": float(cy),
                "confidence": float(conf),
                "normalized_x": float(norm_x),
                "normalized_y": float(norm_y)
            })
            
            success_frames.append(frame_num)
            successful_detections += 1
        else:
            failure_frames.append(frame_num)
        
        detection_results.append(frame_info)
        total_detections += 1
        
        # 显示进度
        if frame_num % 20 == 0 or frame_num == total_frames - 1:
            progress = (frame_num + 1) / total_frames * 100
            print(f"   进度: {progress:.1f}% ({frame_num + 1}/{total_frames})")
    
    cap.release()
    
    # 计算统计信息
    failure_rate = len(failure_frames) / total_frames * 100
    success_rate = len(success_frames) / total_frames * 100
    
    print(f"\n📊 检测统计结果:")
    print(f"   - 总帧数: {total_frames}")
    print(f"   - 成功检测: {len(success_frames)} 帧 ({success_rate:.1f}%)")
    print(f"   - 检测失败: {len(failure_frames)} 帧 ({failure_rate:.1f}%)")
    
    # 分析失败帧的分布
    print(f"\n🔍 失败帧分析:")
    if failure_frames:
        # 连续失败段分析
        failure_segments = []
        current_segment = [failure_frames[0]]
        
        for i in range(1, len(failure_frames)):
            if failure_frames[i] == failure_frames[i-1] + 1:
                current_segment.append(failure_frames[i])
            else:
                failure_segments.append(current_segment)
                current_segment = [failure_frames[i]]
        failure_segments.append(current_segment)
        
        print(f"   - 失败段数: {len(failure_segments)}")
        print(f"   - 最长连续失败: {max(len(seg) for seg in failure_segments)} 帧")
        print(f"   - 最短连续失败: {min(len(seg) for seg in failure_segments)} 帧")
        
        print(f"\n   📋 失败段详情:")
        for i, segment in enumerate(failure_segments):
            start_frame = segment[0]
            end_frame = segment[-1]
            length = len(segment)
            start_time = start_frame / fps
            end_time = end_frame / fps
            print(f"     段 {i+1}: 帧 {start_frame}-{end_frame} ({length}帧) - 时间 {start_time:.1f}s-{end_time:.1f}s")
    
    # 生成报告
    report = {
        "video_info": {
            "filename": os.path.basename(video_path),
            "total_frames": total_frames,
            "fps": fps,
            "width": width,
            "height": height,
            "duration": duration
        },
        "detection_summary": {
            "total_frames": total_frames,
            "successful_detections": len(success_frames),
            "failed_detections": len(failure_frames),
            "success_rate": success_rate,
            "failure_rate": failure_rate
        },
        "failure_analysis": {
            "failure_frames": failure_frames,
            "failure_segments": failure_segments if failure_frames else [],
            "longest_failure_segment": max(len(seg) for seg in failure_segments) if failure_segments else 0,
            "shortest_failure_segment": min(len(seg) for seg in failure_segments) if failure_segments else 0
        },
        "frame_by_frame_results": detection_results,
        "generated_at": datetime.now().isoformat(),
        "model_info": {
            "detector_class": "YOLOv8Detector",
            "fallback_strategy": "disabled",
            "confidence_threshold": "0.05"
        }
    }
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 报告已保存到: {output_file}")
    
    # 生成CSV格式的失败帧列表（便于训练使用）
    csv_file = output_file.replace('.json', '_failure_frames.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("frame_number,timestamp,segment_id\n")
        for i, segment in enumerate(failure_segments):
            for frame_num in segment:
                timestamp = frame_num / fps
                f.write(f"{frame_num},{timestamp:.3f},{i+1}\n")
    
    print(f"📊 失败帧CSV已保存到: {csv_file}")
    
    return report

def main():
    video_path = "/Users/huxiaoran/Desktop/高尔夫测试视频/00001.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 生成报告
    report = analyze_video_detection_failures(video_path)
    
    print(f"\n🎯 训练建议:")
    print(f"   - 重点关注失败率高的帧段")
    print(f"   - 可以针对连续失败段进行数据增强")
    print(f"   - 目标: 将失败率从 {report['detection_summary']['failure_rate']:.1f}% 降低到 <5%")

if __name__ == "__main__":
    main()
