#!/usr/bin/env python3
"""
轨迹优化算法演示脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.trajectory_optimizer import TrajectoryOptimizer
from config.parameters import DEFAULT_CONFIG
import numpy as np
import matplotlib.pyplot as plt


def generate_sample_trajectory(num_frames=100, missing_rate=0.15):
    """
    生成示例轨迹数据
    
    Args:
        num_frames: 总帧数
        missing_rate: 缺失率
        
    Returns:
        示例轨迹数据
    """
    # 生成一个模拟的高尔夫挥杆轨迹
    t = np.linspace(0, 2*np.pi, num_frames)
    
    # 模拟挥杆轨迹（椭圆形状）
    x = 0.5 + 0.3 * np.cos(t) + 0.1 * np.sin(2*t)
    y = 0.5 + 0.2 * np.sin(t) + 0.05 * np.cos(3*t)
    
    # 添加噪声
    noise_x = np.random.normal(0, 0.01, num_frames)
    noise_y = np.random.normal(0, 0.01, num_frames)
    
    x += noise_x
    y += noise_y
    
    # 创建轨迹
    trajectory = []
    for i in range(num_frames):
        if np.random.random() < missing_rate:
            trajectory.append(None)  # 缺失帧
        else:
            trajectory.append((x[i], y[i]))
    
    return trajectory


def visualize_trajectory(original, optimized, title="Trajectory Comparison"):
    """
    可视化轨迹对比
    
    Args:
        original: 原始轨迹
        optimized: 优化后轨迹
        title: 图表标题
    """
    # 分离原始轨迹的有效点
    orig_x = []
    orig_y = []
    for point in original:
        if point is not None:
            orig_x.append(point[0])
            orig_y.append(point[1])
    
    # 分离优化后轨迹的有效点
    opt_x = []
    opt_y = []
    for point in optimized:
        if point is not None:
            opt_x.append(point[0])
            opt_y.append(point[1])
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制原始轨迹
    plt.subplot(2, 2, 1)
    plt.scatter(orig_x, orig_y, c='red', alpha=0.6, s=20, label='Original')
    plt.title('Original Trajectory')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 绘制优化后轨迹
    plt.subplot(2, 2, 2)
    plt.scatter(opt_x, opt_y, c='blue', alpha=0.6, s=20, label='Optimized')
    plt.title('Optimized Trajectory')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 绘制对比图
    plt.subplot(2, 2, 3)
    plt.scatter(orig_x, orig_y, c='red', alpha=0.6, s=20, label='Original')
    plt.scatter(opt_x, opt_y, c='blue', alpha=0.6, s=20, label='Optimized')
    plt.title('Trajectory Comparison')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 绘制轨迹线
    plt.subplot(2, 2, 4)
    if len(orig_x) > 1:
        plt.plot(orig_x, orig_y, 'r-', alpha=0.7, label='Original')
    if len(opt_x) > 1:
        plt.plot(opt_x, opt_y, 'b-', alpha=0.7, label='Optimized')
    plt.title('Trajectory Lines')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """主函数"""
    print("=== 轨迹优化算法演示 ===\n")
    
    # 1. 生成示例数据
    print("1. 生成示例轨迹数据...")
    trajectory = generate_sample_trajectory(num_frames=100, missing_rate=0.15)
    
    # 统计原始数据
    valid_points = sum(1 for point in trajectory if point is not None)
    missing_points = len(trajectory) - valid_points
    detection_rate = valid_points / len(trajectory)
    
    print(f"   总帧数: {len(trajectory)}")
    print(f"   有效帧数: {valid_points}")
    print(f"   缺失帧数: {missing_points}")
    print(f"   检测率: {detection_rate:.2%}")
    
    # 2. 初始化优化器
    print("\n2. 初始化轨迹优化器...")
    optimizer = TrajectoryOptimizer(DEFAULT_CONFIG)
    
    # 3. 优化轨迹
    print("\n3. 开始轨迹优化...")
    optimized_trajectory = optimizer.optimize(trajectory)
    
    # 4. 获取统计信息
    print("\n4. 优化结果统计:")
    stats = optimizer.get_stats()
    print(f"   处理时间: {stats['processing_time']:.3f}秒")
    print(f"   插值帧数: {stats['interpolated_frames']}")
    print(f"   异常值修正: {stats['outliers_removed']}")
    
    # 统计优化后数据
    opt_valid_points = sum(1 for point in optimized_trajectory if point is not None)
    opt_detection_rate = opt_valid_points / len(optimized_trajectory)
    
    print(f"   优化后检测率: {opt_detection_rate:.2%}")
    print(f"   检测率提升: {opt_detection_rate - detection_rate:.2%}")
    
    # 5. 生成优化报告
    print("\n5. 优化报告:")
    print(optimizer.get_optimization_report())
    
    # 6. 可视化结果
    print("\n6. 生成可视化图表...")
    visualize_trajectory(trajectory, optimized_trajectory)
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
