#!/usr/bin/env python3
"""
调试模型管理API
"""

import sys
from pathlib import Path

# 测试路径
MODEL_DIRS = {
    "project": "data",
    "training": "/home/huxiaoran/projects/GolfDetectionModel/GolfDetecitonModel/golf_training_package/golf_detection_wsl_training/results/5090_optimal_training/yolov11x_1280_multiscale_100epochs4/weights"
}

def test_model_scanning():
    """测试模型扫描功能"""
    models = []
    
    # 扫描项目模型目录
    project_dir = Path(MODEL_DIRS["project"])
    print(f"项目目录: {project_dir}")
    print(f"项目目录存在: {project_dir.exists()}")
    
    if project_dir.exists():
        for model_file in project_dir.glob("*.pt"):
            print(f"找到项目模型: {model_file}")
            if model_file.is_file() and model_file.stat().st_size > 1024:
                models.append({
                    "name": model_file.name,
                    "path": str(model_file),
                    "size_mb": round(model_file.stat().st_size / (1024 * 1024), 1),
                    "type": "project"
                })
    
    # 扫描训练模型目录
    training_dir = Path(MODEL_DIRS["training"])
    print(f"训练目录: {training_dir}")
    print(f"训练目录存在: {training_dir.exists()}")
    
    if training_dir.exists():
        for model_file in training_dir.glob("*.pt"):
            print(f"找到训练模型: {model_file}")
            if model_file.is_file():
                models.append({
                    "name": model_file.name,
                    "path": str(model_file),
                    "size_mb": round(model_file.stat().st_size / (1024 * 1024), 1),
                    "type": "training"
                })
    
    print(f"总共找到 {len(models)} 个模型:")
    for model in models:
        print(f"  - {model['name']} ({model['type']}) - {model['size_mb']}MB")

if __name__ == "__main__":
    test_model_scanning()
