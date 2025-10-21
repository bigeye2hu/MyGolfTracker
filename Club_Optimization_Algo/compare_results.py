#!/usr/bin/env python3
"""
轨迹优化前后对比分析脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from algorithms.trajectory_optimizer import TrajectoryOptimizer
from config.parameters import DEFAULT_CONFIG
import numpy as np
import matplotlib.pyplot as plt


def load_real_trajectory():
    """加载真实轨迹数据"""
    # 这是从你之前提供的JSON中提取的真实轨迹数据
    real_trajectory = [
        (0.7476851851851852, 0.734375),
        (0.7476851851851852, 0.734375),
        (0.7453703703703703, 0.7317708333333334),
        (0.7476851851851852, 0.7317708333333334),
        (0.7476851851851852, 0.73046875),
        (0.7476851851851852, 0.73046875),
        (0.7476851851851852, 0.73046875),
        (0.7476851851851852, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.7291666666666666),
        (0.75, 0.7291666666666666),
        (0.75, 0.7291666666666666),
        (0.75, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.7523148148148148, 0.7291666666666666),
        (0.75, 0.7291666666666666),
        (0.75, 0.7291666666666666),
        (0.75, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.73046875),
        (0.75, 0.7317708333333334),
        (0.75, 0.734375),
        (0.75, 0.734375),
        (0.75, 0.734375),
        (0.75, 0.7356770833333334),
        (0.75, 0.7356770833333334),
        (0.7523148148148148, 0.7356770833333334),
        (0.75, 0.7369791666666666),
        (0.7523148148148148, 0.7369791666666666),
        (0.75, 0.73828125),
        (0.7523148148148148, 0.73828125),
        (0.7546296296296297, 0.73828125),
        (0.7569444444444444, 0.7395833333333334),
        (0.7569444444444444, 0.7408854166666666),
        (0.7638888888888888, 0.7421875),
        (0.7638888888888888, 0.7434895833333334),
        (0.7638888888888888, 0.7447916666666666),
        (0.7638888888888888, 0.7447916666666666),
        (0.7638888888888888, 0.7447916666666666),
        (0.7685185185185185, 0.7421875),
        (0.7569444444444444, 0.7421875),
        None,  # 缺失帧
        (0.7569444444444444, 0.7265625),
        (0.7476851851851852, 0.7135416666666666),
        (0.7314814814814815, 0.7005208333333334),
        (0.7013888888888888, 0.6744791666666666),
        (0.6805555555555556, 0.6471354166666666),
        (0.6134259259259259, 0.6119791666666666),
        (0.5902777777777778, 0.59765625),
        (0.1597222222222222, 0.5533854166666666),
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        (0.24074074074074073, 0.32421875),
        (0.18518518518518517, 0.2786458333333333),
        (0.1412037037037037, 0.23828125),
        (0.11342592592592593, 0.203125),
        (0.09953703703703703, 0.17838541666666666),
        (0.09490740740740741, 0.15755208333333334),
        (0.10185185185185185, 0.14583333333333334),
        (0.12268518518518519, 0.1484375),
        (0.14814814814814814, 0.14973958333333334),
        (0.18055555555555555, 0.15885416666666666),
        (0.2152777777777778, 0.17057291666666666),
        (0.2569444444444444, 0.19270833333333334),
        (0.30092592592592593, 0.23307291666666666),
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        (0.42824074074074076, 0.2825520833333333),
        (0.4305555555555556, 0.2825520833333333),
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        (0.25925925925925924, 0.16276041666666666),
        (0.23842592592592593, 0.16796875),
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        None,  # 缺失帧
        (0.6064814814814815, 0.5859375),
        (0.5787037037037037, 0.5572916666666666),
        None,  # 缺失帧
        (0.18055555555555555, 0.15755208333333334),
        (0.19675925925925927, 0.13020833333333334),
        (0.4861111111111111, 0.34375),
        None,  # 缺失帧
        None,  # 缺失帧
        (0.4583333333333333, 0.23177083333333334),
        (0.5023148148148148, 0.24869791666666666),
        (0.5370370370370371, 0.2526041666666667),
        (0.5578703703703703, 0.24609375),
        (0.5671296296296297, 0.234375),
        (0.5763888888888888, 0.21875),
        (0.5787037037037037, 0.203125),
        (0.5740740740740741, 0.19010416666666666),
        (0.5694444444444444, 0.18098958333333334),
        (0.5671296296296297, 0.17447916666666666),
        (0.5648148148148148, 0.17057291666666666),
        (0.5648148148148148, 0.16796875),
        (0.5625, 0.16536458333333334),
        (0.5625, 0.16536458333333334),
        (0.5671296296296297, 0.16536458333333334),
        (0.5694444444444444, 0.16536458333333334),
        (0.5717592592592593, 0.16536458333333334),
        (0.5717592592592593, 0.16536458333333334),
        (0.5717592592592593, 0.1640625),
        (0.5717592592592593, 0.16276041666666666),
        (0.5717592592592593, 0.16145833333333334),
        (0.5671296296296297, 0.15885416666666666),
        (0.5578703703703703, 0.15494791666666666),
        (0.5509259259259259, 0.15234375),
        (0.5439814814814815, 0.14453125),
        (0.5300925925925926, 0.14192708333333334),
        (0.5185185185185185, 0.13932291666666666),
        (0.5046296296296297, 0.140625),
        (0.4930555555555556, 0.13802083333333334),
        (0.48148148148148145, 0.13932291666666666),
        (0.46296296296296297, 0.140625),
        (0.44907407407407407, 0.15364583333333334),
        (0.4351851851851852, 0.16145833333333334),
        (0.4212962962962963, 0.17447916666666666),
        (0.4166666666666667, 0.19270833333333334),
        None  # 缺失帧
    ]
    return real_trajectory


def analyze_trajectory(trajectory, name):
    """分析轨迹数据"""
    print(f"\n=== {name} 分析 ===")
    
    # 基本统计
    total_frames = len(trajectory)
    valid_frames = sum(1 for point in trajectory if point is not None)
    missing_frames = total_frames - valid_frames
    detection_rate = valid_frames / total_frames
    
    print(f"总帧数: {total_frames}")
    print(f"有效帧数: {valid_frames}")
    print(f"缺失帧数: {missing_frames}")
    print(f"检测率: {detection_rate:.2%}")
    
    if valid_frames < 2:
        print("有效帧数不足，无法进行进一步分析")
        return {}
    
    # 获取有效点
    valid_points = [point for point in trajectory if point is not None]
    x_coords = [point[0] for point in valid_points]
    y_coords = [point[1] for point in valid_points]
    
    # 计算轨迹统计
    distances = []
    for i in range(1, len(x_coords)):
        dx = x_coords[i] - x_coords[i-1]
        dy = y_coords[i] - y_coords[i-1]
        distance = np.sqrt(dx*dx + dy*dy)
        distances.append(distance)
    
    velocities = distances.copy()
    accelerations = [velocities[i] - velocities[i-1] for i in range(1, len(velocities))]
    
    # 统计信息
    total_distance = sum(distances)
    avg_velocity = np.mean(velocities) if velocities else 0.0
    max_velocity = max(velocities) if velocities else 0.0
    avg_acceleration = np.mean(accelerations) if accelerations else 0.0
    max_acceleration = max(accelerations) if accelerations else 0.0
    
    print(f"总距离: {total_distance:.6f}")
    print(f"平均速度: {avg_velocity:.6f}")
    print(f"最大速度: {max_velocity:.6f}")
    print(f"平均加速度: {avg_acceleration:.6f}")
    print(f"最大加速度: {max_acceleration:.6f}")
    
    # 坐标范围
    x_range = (min(x_coords), max(x_coords))
    y_range = (min(y_coords), max(y_coords))
    print(f"X坐标范围: {x_range[0]:.6f} - {x_range[1]:.6f}")
    print(f"Y坐标范围: {y_range[0]:.6f} - {y_range[1]:.6f}")
    
    return {
        'total_frames': total_frames,
        'valid_frames': valid_frames,
        'missing_frames': missing_frames,
        'detection_rate': detection_rate,
        'total_distance': total_distance,
        'avg_velocity': avg_velocity,
        'max_velocity': max_velocity,
        'avg_acceleration': avg_acceleration,
        'max_acceleration': max_acceleration,
        'x_range': x_range,
        'y_range': y_range,
        'valid_points': valid_points
    }


def compare_trajectories(original_stats, optimized_stats):
    """对比两个轨迹的统计信息"""
    print(f"\n=== 对比分析 ===")
    
    # 检测率对比
    detection_rate_improvement = optimized_stats['detection_rate'] - original_stats['detection_rate']
    print(f"检测率提升: {detection_rate_improvement:.2%}")
    
    # 距离对比
    distance_change = optimized_stats['total_distance'] - original_stats['total_distance']
    distance_change_pct = (distance_change / original_stats['total_distance']) * 100 if original_stats['total_distance'] > 0 else 0
    print(f"总距离变化: {distance_change:.6f} ({distance_change_pct:+.2f}%)")
    
    # 速度对比
    velocity_change = optimized_stats['avg_velocity'] - original_stats['avg_velocity']
    velocity_change_pct = (velocity_change / original_stats['avg_velocity']) * 100 if original_stats['avg_velocity'] > 0 else 0
    print(f"平均速度变化: {velocity_change:.6f} ({velocity_change_pct:+.2f}%)")
    
    # 加速度对比
    acceleration_change = optimized_stats['avg_acceleration'] - original_stats['avg_acceleration']
    acceleration_change_pct = (acceleration_change / original_stats['avg_acceleration']) * 100 if original_stats['avg_acceleration'] != 0 else 0
    print(f"平均加速度变化: {acceleration_change:.6f} ({acceleration_change_pct:+.2f}%)")
    
    # 坐标范围对比
    x_range_original = original_stats['x_range']
    x_range_optimized = optimized_stats['x_range']
    y_range_original = original_stats['y_range']
    y_range_optimized = optimized_stats['y_range']
    
    print(f"X坐标范围变化: {x_range_original[0]:.6f}-{x_range_original[1]:.6f} → {x_range_optimized[0]:.6f}-{x_range_optimized[1]:.6f}")
    print(f"Y坐标范围变化: {y_range_original[0]:.6f}-{y_range_original[1]:.6f} → {y_range_optimized[0]:.6f}-{y_range_optimized[1]:.6f}")


def visualize_comparison(original_trajectory, optimized_trajectory):
    """可视化对比"""
    # 分离原始轨迹的有效点
    orig_x = []
    orig_y = []
    for point in original_trajectory:
        if point is not None:
            orig_x.append(point[0])
            orig_y.append(point[1])
    
    # 分离优化后轨迹的有效点
    opt_x = []
    opt_y = []
    for point in optimized_trajectory:
        if point is not None:
            opt_x.append(point[0])
            opt_y.append(point[1])
    
    # 创建对比图
    plt.figure(figsize=(15, 10))
    
    # 1. 轨迹对比
    plt.subplot(2, 3, 1)
    plt.scatter(orig_x, orig_y, c='red', alpha=0.6, s=20, label='Original')
    plt.scatter(opt_x, opt_y, c='blue', alpha=0.6, s=20, label='Optimized')
    plt.title('Trajectory Comparison')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. 原始轨迹
    plt.subplot(2, 3, 2)
    plt.scatter(orig_x, orig_y, c='red', alpha=0.6, s=20)
    plt.title('Original Trajectory')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True, alpha=0.3)
    
    # 3. 优化轨迹
    plt.subplot(2, 3, 3)
    plt.scatter(opt_x, opt_y, c='blue', alpha=0.6, s=20)
    plt.title('Optimized Trajectory')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True, alpha=0.3)
    
    # 4. 轨迹线对比
    plt.subplot(2, 3, 4)
    if len(orig_x) > 1:
        plt.plot(orig_x, orig_y, 'r-', alpha=0.7, label='Original')
    if len(opt_x) > 1:
        plt.plot(opt_x, opt_y, 'b-', alpha=0.7, label='Optimized')
    plt.title('Trajectory Lines')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 5. 检测率对比
    plt.subplot(2, 3, 5)
    detection_rates = ['Original', 'Optimized']
    rates = [len(orig_x)/len(original_trajectory), len(opt_x)/len(optimized_trajectory)]
    colors = ['red', 'blue']
    bars = plt.bar(detection_rates, rates, color=colors, alpha=0.7)
    plt.title('Detection Rate Comparison')
    plt.ylabel('Detection Rate')
    plt.ylim(0, 1)
    for bar, rate in zip(bars, rates):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{rate:.2%}', ha='center', va='bottom')
    plt.grid(True, alpha=0.3)
    
    # 6. 帧数对比
    plt.subplot(2, 3, 6)
    frame_counts = ['Original', 'Optimized']
    counts = [len(orig_x), len(opt_x)]
    colors = ['red', 'blue']
    bars = plt.bar(frame_counts, counts, color=colors, alpha=0.7)
    plt.title('Valid Frames Comparison')
    plt.ylabel('Frame Count')
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{count}', ha='center', va='bottom')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """主函数"""
    print("=== 轨迹优化前后对比分析 ===\n")
    
    # 1. 加载原始轨迹
    print("1. 加载原始轨迹数据...")
    original_trajectory = load_real_trajectory()
    
    # 2. 分析原始轨迹
    original_stats = analyze_trajectory(original_trajectory, "原始轨迹")
    
    # 3. 优化轨迹
    print("\n2. 开始轨迹优化...")
    optimizer = TrajectoryOptimizer(DEFAULT_CONFIG)
    optimized_trajectory = optimizer.optimize(original_trajectory)
    
    # 4. 分析优化后轨迹
    optimized_stats = analyze_trajectory(optimized_trajectory, "优化轨迹")
    
    # 5. 对比分析
    compare_trajectories(original_stats, optimized_stats)
    
    # 6. 获取优化统计
    print(f"\n=== 优化统计 ===")
    stats = optimizer.get_stats()
    print(f"处理时间: {stats['processing_time']:.3f}秒")
    print(f"插值帧数: {stats['interpolated_frames']}")
    print(f"异常值修正: {stats['outliers_removed']}")
    
    # 7. 生成优化报告
    print(f"\n=== 优化报告 ===")
    print(optimizer.get_optimization_report())
    
    # 8. 可视化对比
    print(f"\n8. 生成可视化对比图...")
    visualize_comparison(original_trajectory, optimized_trajectory)
    
    print(f"\n=== 对比分析完成 ===")


if __name__ == "__main__":
    main()
