#!/usr/bin/env python3
"""
在Docker容器中测试新模型
"""

import sys
import time
import numpy as np

def test_model():
    try:
        from ultralytics import YOLO
        
        print("🔍 测试新模型...")
        
        # 加载模型
        model = YOLO("data/best.pt")
        print("✅ 模型加载成功")
        print(f"📋 类别: {model.names}")
        
        # 测试推理
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        print("⏳ 执行推理...")
        
        start_time = time.time()
        results = model(test_image, conf=0.01, iou=0.7, max_det=10, verbose=False)
        inference_time = time.time() - start_time
        
        print(f"✅ 推理完成，耗时: {inference_time:.3f}秒")
        
        if results and len(results) > 0:
            result = results[0]
            detections = len(result.boxes) if result.boxes is not None else 0
            print(f"🎯 检测到 {detections} 个目标")
        
        print("🎉 新模型测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_model()
    sys.exit(0 if success else 1)
