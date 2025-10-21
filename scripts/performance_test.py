#!/usr/bin/env python3
"""
性能测试脚本 - 比较本地CPU和远程GPU的处理速度
"""
import os
import sys
import time
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_local_performance(video_path: str):
    """测试本地CPU性能"""
    print("🖥️  开始本地CPU性能测试...")
    
    # 启动本地服务（如果未运行）
    try:
        response = requests.get("http://localhost:5005/health", timeout=5)
        if response.status_code != 200:
            print("❌ 本地服务未运行，请先启动服务")
            return None
    except requests.exceptions.RequestException:
        print("❌ 本地服务未运行，请先启动服务")
        return None
    
    # 上传视频进行分析
    start_time = time.time()
    
    with open(video_path, 'rb') as f:
        files = {'video': f}
        data = {
            'resolution': '480',
            'confidence': '0.01',
            'iou': '0.7',
            'max_det': '10',
            'optimization_strategy': 'original'
        }
        
        try:
            response = requests.post(
                "http://localhost:5005/analyze/video",
                files=files,
                data=data,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                
                # 轮询任务状态
                while True:
                    status_response = requests.get(f"http://localhost:5005/analyze/video/status?job_id={job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'done':
                            end_time = time.time()
                            processing_time = end_time - start_time
                            
                            result_data = status_data.get('result', {})
                            total_frames = result_data.get('total_frames', 0)
                            detected_frames = result_data.get('detected_frames', 0)
                            detection_rate = result_data.get('detection_rate', 0)
                            
                            print(f"✅ 本地CPU测试完成")
                            print(f"   处理时间: {processing_time:.2f}秒")
                            print(f"   总帧数: {total_frames}")
                            print(f"   检测帧数: {detected_frames}")
                            print(f"   检测率: {detection_rate}%")
                            print(f"   平均每帧处理时间: {processing_time/total_frames*1000:.2f}ms")
                            
                            return {
                                'type': 'local_cpu',
                                'processing_time': processing_time,
                                'total_frames': total_frames,
                                'detected_frames': detected_frames,
                                'detection_rate': detection_rate,
                                'avg_time_per_frame': processing_time/total_frames*1000
                            }
                        elif status_data.get('status') == 'error':
                            print(f"❌ 本地测试失败: {status_data.get('error')}")
                            return None
                    
                    time.sleep(1)
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 本地测试请求失败: {e}")
            return None

def test_remote_gpu_performance(video_path: str, server_ip: str):
    """测试远程GPU性能"""
    print(f"🚀 开始远程GPU性能测试 (服务器: {server_ip})...")
    
    # 检查远程服务状态
    try:
        response = requests.get(f"http://{server_ip}:5005/health", timeout=10)
        if response.status_code != 200:
            print("❌ 远程服务不可用")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到远程服务: {e}")
        return None
    
    # 上传视频进行分析
    start_time = time.time()
    
    with open(video_path, 'rb') as f:
        files = {'video': f}
        data = {
            'resolution': '480',
            'confidence': '0.01',
            'iou': '0.7',
            'max_det': '10',
            'optimization_strategy': 'original'
        }
        
        try:
            response = requests.post(
                f"http://{server_ip}:5005/analyze/video",
                files=files,
                data=data,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                
                # 轮询任务状态
                while True:
                    status_response = requests.get(f"http://{server_ip}:5005/analyze/video/status?job_id={job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'done':
                            end_time = time.time()
                            processing_time = end_time - start_time
                            
                            result_data = status_data.get('result', {})
                            total_frames = result_data.get('total_frames', 0)
                            detected_frames = result_data.get('detected_frames', 0)
                            detection_rate = result_data.get('detection_rate', 0)
                            
                            print(f"✅ 远程GPU测试完成")
                            print(f"   处理时间: {processing_time:.2f}秒")
                            print(f"   总帧数: {total_frames}")
                            print(f"   检测帧数: {detected_frames}")
                            print(f"   检测率: {detection_rate}%")
                            print(f"   平均每帧处理时间: {processing_time/total_frames*1000:.2f}ms")
                            
                            return {
                                'type': 'remote_gpu',
                                'processing_time': processing_time,
                                'total_frames': total_frames,
                                'detected_frames': detected_frames,
                                'detection_rate': detection_rate,
                                'avg_time_per_frame': processing_time/total_frames*1000
                            }
                        elif status_data.get('status') == 'error':
                            print(f"❌ 远程测试失败: {status_data.get('error')}")
                            return None
                    
                    time.sleep(1)
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 远程测试请求失败: {e}")
            return None

def compare_results(local_result, remote_result):
    """比较测试结果"""
    if not local_result or not remote_result:
        print("❌ 无法比较结果，测试数据不完整")
        return
    
    print("\n" + "="*60)
    print("📊 性能对比结果")
    print("="*60)
    
    # 处理时间对比
    local_time = local_result['processing_time']
    remote_time = remote_result['processing_time']
    speedup = local_time / remote_time if remote_time > 0 else 0
    
    print(f"⏱️  处理时间对比:")
    print(f"   本地CPU: {local_time:.2f}秒")
    print(f"   远程GPU: {remote_time:.2f}秒")
    print(f"   GPU加速比: {speedup:.2f}x")
    
    # 每帧处理时间对比
    local_avg = local_result['avg_time_per_frame']
    remote_avg = remote_result['avg_time_per_frame']
    
    print(f"\n🎯 每帧处理时间对比:")
    print(f"   本地CPU: {local_avg:.2f}ms/帧")
    print(f"   远程GPU: {remote_avg:.2f}ms/帧")
    print(f"   GPU加速比: {local_avg/remote_avg:.2f}x")
    
    # 检测率对比
    local_detection = local_result['detection_rate']
    remote_detection = remote_result['detection_rate']
    
    print(f"\n🎯 检测率对比:")
    print(f"   本地CPU: {local_detection:.2f}%")
    print(f"   远程GPU: {remote_detection:.2f}%")
    print(f"   差异: {abs(local_detection - remote_detection):.2f}%")
    
    # 总结
    print(f"\n📈 总结:")
    if speedup > 1:
        print(f"   🚀 GPU比CPU快 {speedup:.2f} 倍")
    else:
        print(f"   ⚠️  GPU比CPU慢 {1/speedup:.2f} 倍")
    
    if abs(local_detection - remote_detection) < 1:
        print(f"   ✅ 检测精度基本一致")
    else:
        print(f"   ⚠️  检测精度存在差异")

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python performance_test.py <视频文件路径> <远程服务器IP>")
        print("示例: python performance_test.py test_video.mp4 101.132.66.247")
        sys.exit(1)
    
    video_path = sys.argv[1]
    server_ip = sys.argv[2]
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        sys.exit(1)
    
    print("🎬 开始性能测试...")
    print(f"📁 测试视频: {video_path}")
    print(f"🌐 远程服务器: {server_ip}")
    print("-" * 60)
    
    # 测试本地性能
    local_result = test_local_performance(video_path)
    
    print("\n" + "-" * 60)
    
    # 测试远程性能
    remote_result = test_remote_gpu_performance(video_path, server_ip)
    
    # 比较结果
    compare_results(local_result, remote_result)

if __name__ == "__main__":
    main()

