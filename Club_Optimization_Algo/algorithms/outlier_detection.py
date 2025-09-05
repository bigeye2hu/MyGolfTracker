#!/usr/bin/env python3
"""
异常值检测算法
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy import stats


class OutlierDetector:
    """异常值检测器"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def detect(self, trajectory: List[Tuple[float, float]]) -> List[int]:
        """
        检测轨迹中的异常值
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            异常值索引列表
        """
        if len(trajectory) < 3:
            return []
        
        # 获取有效点
        valid_points = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                valid_points.append(point)
                valid_indices.append(i)
        
        if len(valid_points) < 3:
            return []
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 使用多种方法检测异常值
        outliers = set()
        
        # 1. Z-score方法
        z_score_outliers = self._detect_z_score_outliers(x_coords, y_coords, valid_indices)
        outliers.update(z_score_outliers)
        
        # 2. IQR方法
        iqr_outliers = self._detect_iqr_outliers(x_coords, y_coords, valid_indices)
        outliers.update(iqr_outliers)
        
        # 3. 距离方法
        distance_outliers = self._detect_distance_outliers(x_coords, y_coords, valid_indices)
        outliers.update(distance_outliers)
        
        # 4. 速度方法
        velocity_outliers = self._detect_velocity_outliers(x_coords, y_coords, valid_indices)
        outliers.update(velocity_outliers)
        
        return sorted(list(outliers))
    
    def _detect_z_score_outliers(self, x_coords: List[float], y_coords: List[float], 
                                valid_indices: List[int]) -> List[int]:
        """使用Z-score方法检测异常值"""
        outliers = []
        
        # 计算Z-score
        x_z_scores = np.abs(stats.zscore(x_coords))
        y_z_scores = np.abs(stats.zscore(y_coords))
        
        threshold = self.config.get('z_score_threshold', 2.5)
        
        for i, (x_z, y_z) in enumerate(zip(x_z_scores, y_z_scores)):
            if x_z > threshold or y_z > threshold:
                outliers.append(valid_indices[i])
        
        return outliers
    
    def _detect_iqr_outliers(self, x_coords: List[float], y_coords: List[float], 
                           valid_indices: List[int]) -> List[int]:
        """使用IQR方法检测异常值"""
        outliers = []
        
        # 计算IQR
        x_q1, x_q3 = np.percentile(x_coords, [25, 75])
        y_q1, y_q3 = np.percentile(y_coords, [25, 75])
        
        x_iqr = x_q3 - x_q1
        y_iqr = y_q3 - y_q1
        
        multiplier = self.config.get('iqr_multiplier', 1.5)
        
        x_lower_bound = x_q1 - multiplier * x_iqr
        x_upper_bound = x_q3 + multiplier * x_iqr
        y_lower_bound = y_q1 - multiplier * y_iqr
        y_upper_bound = y_q3 + multiplier * y_iqr
        
        for i, (x, y) in enumerate(zip(x_coords, y_coords)):
            if (x < x_lower_bound or x > x_upper_bound or 
                y < y_lower_bound or y > y_upper_bound):
                outliers.append(valid_indices[i])
        
        return outliers
    
    def _detect_distance_outliers(self, x_coords: List[float], y_coords: List[float], 
                                valid_indices: List[int]) -> List[int]:
        """使用距离方法检测异常值"""
        outliers = []
        
        if len(x_coords) < 3:
            return outliers
        
        # 计算每个点到其邻居的平均距离
        distances = []
        for i in range(len(x_coords)):
            if i == 0:
                # 第一个点，只计算到下一个点的距离
                dist = np.sqrt((x_coords[i+1] - x_coords[i])**2 + 
                             (y_coords[i+1] - y_coords[i])**2)
            elif i == len(x_coords) - 1:
                # 最后一个点，只计算到前一个点的距离
                dist = np.sqrt((x_coords[i] - x_coords[i-1])**2 + 
                             (y_coords[i] - y_coords[i-1])**2)
            else:
                # 中间点，计算到前后两个点的平均距离
                dist1 = np.sqrt((x_coords[i] - x_coords[i-1])**2 + 
                               (y_coords[i] - y_coords[i-1])**2)
                dist2 = np.sqrt((x_coords[i+1] - x_coords[i])**2 + 
                               (y_coords[i+1] - y_coords[i])**2)
                dist = (dist1 + dist2) / 2
            
            distances.append(dist)
        
        # 计算距离的统计信息
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        
        threshold = self.config.get('distance_threshold', 0.2)
        
        for i, dist in enumerate(distances):
            if dist > mean_dist + threshold * std_dist:
                outliers.append(valid_indices[i])
        
        return outliers
    
    def _detect_velocity_outliers(self, x_coords: List[float], y_coords: List[float], 
                                valid_indices: List[int]) -> List[int]:
        """使用速度方法检测异常值"""
        outliers = []
        
        if len(x_coords) < 3:
            return outliers
        
        # 计算速度
        velocities = []
        for i in range(1, len(x_coords)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            velocity = np.sqrt(dx*dx + dy*dy)
            velocities.append(velocity)
        
        if len(velocities) < 2:
            return outliers
        
        # 计算速度的统计信息
        mean_velocity = np.mean(velocities)
        std_velocity = np.std(velocities)
        
        threshold = self.config.get('velocity_threshold', 0.15)
        
        for i, velocity in enumerate(velocities):
            if velocity > mean_velocity + threshold * std_velocity:
                # 标记速度异常的点
                outliers.append(valid_indices[i+1])  # i+1因为速度对应的是第二个点
        
        return outliers
    
    def get_outlier_statistics(self, trajectory: List[Tuple[float, float]]) -> dict:
        """
        获取异常值统计信息
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            异常值统计信息
        """
        outliers = self.detect(trajectory)
        
        # 获取有效点
        valid_points = []
        for point in trajectory:
            if point is not None:
                valid_points.append(point)
        
        if len(valid_points) < 3:
            return {
                'total_points': len(trajectory),
                'valid_points': len(valid_points),
                'outliers': len(outliers),
                'outlier_rate': 0.0
            }
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 计算统计信息
        x_mean = np.mean(x_coords)
        y_mean = np.mean(y_coords)
        x_std = np.std(x_coords)
        y_std = np.std(y_coords)
        
        return {
            'total_points': len(trajectory),
            'valid_points': len(valid_points),
            'outliers': len(outliers),
            'outlier_rate': len(outliers) / len(valid_points) if valid_points else 0.0,
            'x_mean': x_mean,
            'y_mean': y_mean,
            'x_std': x_std,
            'y_std': y_std,
            'outlier_indices': outliers
        }
