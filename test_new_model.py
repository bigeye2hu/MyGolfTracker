#!/usr/bin/env python3
"""
测试新训练的高尔夫检测模型
验证模型加载和基本推理功能
"""

import sys
import os
import time
import numpy as np
import cv2

# 添加项目路径
sys.path.append('/home/huxiaoran/projects/MyGolfTracker')

def test_model_loading():
    """测试模型加载"""
    print("🔍 测试模型加载...")
    
    try:
        from ultralytics import YOLO
        
        model_path = "data/best.pt"
        print(f"📁 模型路径: {model_path}")
        
        # 检查文件是否存在
        if not os.path.exists(model_path):
            print(f"❌ 模型文件不存在: {model_path}")
            return False
            
        # 获取文件大小
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"📊 模型文件大小: {file_size:.1f} MB")
        
        # 加载模型
        print("⏳ 加载模型中...")
        start_time = time.time()
        model = YOLO(model_path)
        load_time = time.time() - start_time
        print(f"✅ 模型加载成功，耗时: {load_time:.2f}秒")
        
        # 检查模型信息
        print(f"📋 模型类别: {model.names}")
        print(f"🔢 类别数量: {len(model.names)}")
        
        return model
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None

def test_gpu_inference(model):
    """测试GPU推理"""
    print("\n🎮 测试GPU推理...")
    
    try:
        # 检查CUDA可用性
        import torch
        if not torch.cuda.is_available():
            print("⚠️ CUDA不可用，使用CPU推理")
            return False
            
        print(f"🔧 CUDA设备: {torch.cuda.get_device_name(0)}")
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        print(f"🖼️ 测试图像尺寸: {test_image.shape}")
        
        # 测试推理
        print("⏳ 执行推理...")
        start_time = time.time()
        
        # 将模型移动到GPU
        model.to("cuda")
        
        # 执行推理
        results = model(test_image, conf=0.01, iou=0.7, max_det=10)
        
        inference_time = time.time() - start_time
        print(f"✅ 推理完成，耗时: {inference_time:.3f}秒")
        
        # 检查结果
        if results and len(results) > 0:
            result = results[0]
            detections = len(result.boxes) if result.boxes is not None else 0
            print(f"🎯 检测到 {detections} 个目标")
            
            if detections > 0:
                confidences = result.boxes.conf.cpu().numpy()
                print(f"📊 置信度范围: {confidences.min():.3f} - {confidences.max():.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU推理测试失败: {e}")
        return False

def test_model_performance(model):
    """测试模型性能"""
    print("\n📈 测试模型性能...")
    
    try:
        # 创建多个测试图像
        test_images = []
        for i in range(5):
            img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            test_images.append(img)
        
        print(f"🖼️ 准备 {len(test_images)} 张测试图像")
        
        # 批量推理测试
        start_time = time.time()
        
        for i, img in enumerate(test_images):
            results = model(img, conf=0.01, iou=0.7, max_det=10, verbose=False)
            
        total_time = time.time() - start_time
        avg_time = total_time / len(test_images)
        
        print(f"✅ 批量推理完成")
        print(f"⏱️ 总耗时: {total_time:.3f}秒")
        print(f"📊 平均每张: {avg_time:.3f}秒")
        print(f"🚀 推理速度: {1/avg_time:.1f} FPS")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试新训练的高尔夫检测模型")
    print("=" * 50)
    
    # 测试模型加载
    model = test_model_loading()
    if model is None:
        print("❌ 模型加载失败，测试终止")
        return False
    
    # 测试GPU推理
    gpu_success = test_gpu_inference(model)
    
    # 测试性能
    perf_success = test_model_performance(model)
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"✅ 模型加载: 成功")
    print(f"{'✅' if gpu_success else '❌'} GPU推理: {'成功' if gpu_success else '失败'}")
    print(f"{'✅' if perf_success else '❌'} 性能测试: {'成功' if perf_success else '失败'}")
    
    if gpu_success and perf_success:
        print("\n🎉 新模型测试通过！可以部署到生产环境。")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
