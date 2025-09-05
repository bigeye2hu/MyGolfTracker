#!/usr/bin/env python3
"""
数据处理工具
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any


class TrajectoryProcessor:
    """轨迹数据处理器"""
    
    def __init__(self):
        pass
    
    def normalize_trajectory(self, trajectory: List[Tuple[float, float]], 
                           width: int, height: int) -> List[Tuple[float, float]]:
        """
        将轨迹坐标归一化到[0,1]范围
        
        Args:
            trajectory: 原始轨迹
            width: 视频宽度
            height: 视频高度
            
        Returns:
            归一化后的轨迹
        """
        normalized = []
        for point in trajectory:
            if point is not None:
                x_norm = point[0] / width
                y_norm = point[1] / height
                normalized.append((x_norm, y_norm))
            else:
                normalized.append(None)
        
        return normalized
    
    def denormalize_trajectory(self, trajectory: List[Tuple[float, float]], 
                             width: int, height: int) -> List[Tuple[float, float]]:
        """
        将归一化轨迹转换回像素坐标
        
        Args:
            trajectory: 归一化轨迹
            width: 视频宽度
            height: 视频高度
            
        Returns:
            像素坐标轨迹
        """
        denormalized = []
        for point in trajectory:
            if point is not None:
                x_pixel = point[0] * width
                y_pixel = point[1] * height
                denormalized.append((x_pixel, y_pixel))
            else:
                denormalized.append(None)
        
        return denormalized
    
    def filter_trajectory(self, trajectory: List[Tuple[float, float]], 
                         min_distance: float = 0.001) -> List[Tuple[float, float]]:
        """
        过滤轨迹中的重复点
        
        Args:
            trajectory: 轨迹数据
            min_distance: 最小距离阈值
            
        Returns:
            过滤后的轨迹
        """
        if len(trajectory) < 2:
            return trajectory.copy()
        
        filtered = [trajectory[0]]  # 保留第一个点
        
        for i in range(1, len(trajectory)):
            if trajectory[i] is None:
                filtered.append(None)
                continue
            
            prev_point = filtered[-1]
            if prev_point is None:
                filtered.append(trajectory[i])
                continue
            
            # 计算距离
            dx = trajectory[i][0] - prev_point[0]
            dy = trajectory[i][1] - prev_point[1]
            distance = np.sqrt(dx*dx + dy*dy)
            
            # 如果距离大于阈值，保留该点
            if distance >= min_distance:
                filtered.append(trajectory[i])
            else:
                # 距离太小，跳过该点
                continue
        
        return filtered
    
    def resample_trajectory(self, trajectory: List[Tuple[float, float]], 
                           target_length: int) -> List[Tuple[float, float]]:
        """
        重采样轨迹到目标长度
        
        Args:
            trajectory: 原始轨迹
            target_length: 目标长度
            
        Returns:
            重采样后的轨迹
        """
        if len(trajectory) == target_length:
            return trajectory.copy()
        
        # 获取有效点
        valid_points = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                valid_points.append(point)
                valid_indices.append(i)
        
        if len(valid_points) < 2:
            return trajectory.copy()
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 创建新的索引
        old_indices = np.linspace(0, len(trajectory) - 1, len(trajectory))
        new_indices = np.linspace(0, len(trajectory) - 1, target_length)
        
        # 插值
        from scipy.interpolate import interp1d
        
        x_interp = interp1d(old_indices, x_coords, kind='linear', 
                           bounds_error=False, fill_value='extrapolate')
        y_interp = interp1d(old_indices, y_coords, kind='linear', 
                           bounds_error=False, fill_value='extrapolate')
        
        # 生成新轨迹
        resampled = []
        for i in range(target_length):
            x = float(x_interp(i))
            y = float(y_interp(i))
            resampled.append((x, y))
        
        return resampled
    
    def calculate_trajectory_statistics(self, trajectory: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        计算轨迹统计信息
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            统计信息字典
        """
        # 获取有效点
        valid_points = []
        for point in trajectory:
            if point is not None:
                valid_points.append(point)
        
        if len(valid_points) < 2:
            return {
                'total_frames': len(trajectory),
                'valid_frames': len(valid_points),
                'detection_rate': 0.0,
                'total_distance': 0.0,
                'avg_velocity': 0.0,
                'max_velocity': 0.0,
                'avg_acceleration': 0.0,
                'max_acceleration': 0.0
            }
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 计算距离
        distances = []
        for i in range(1, len(x_coords)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            distance = np.sqrt(dx*dx + dy*dy)
            distances.append(distance)
        
        # 计算速度
        velocities = distances.copy()
        
        # 计算加速度
        accelerations = []
        for i in range(1, len(velocities)):
            acceleration = velocities[i] - velocities[i-1]
            accelerations.append(acceleration)
        
        # 统计信息
        total_distance = sum(distances)
        avg_velocity = np.mean(velocities) if velocities else 0.0
        max_velocity = max(velocities) if velocities else 0.0
        avg_acceleration = np.mean(accelerations) if accelerations else 0.0
        max_acceleration = max(accelerations) if accelerations else 0.0
        
        return {
            'total_frames': len(trajectory),
            'valid_frames': len(valid_points),
            'detection_rate': len(valid_points) / len(trajectory),
            'total_distance': total_distance,
            'avg_velocity': avg_velocity,
            'max_velocity': max_velocity,
            'avg_acceleration': avg_acceleration,
            'max_acceleration': max_acceleration,
            'x_range': (min(x_coords), max(x_coords)),
            'y_range': (min(y_coords), max(y_coords))
        }
