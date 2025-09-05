#!/usr/bin/env python3
"""
轨迹插值算法
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy.interpolate import interp1d, CubicSpline


class BaseInterpolator:
    """插值算法基类"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def interpolate(self, trajectory: List[Tuple[float, float]], 
                   missing_indices: List[int]) -> List[Tuple[float, float]]:
        """
        插值填充缺失帧
        
        Args:
            trajectory: 轨迹数据
            missing_indices: 缺失帧索引列表
            
        Returns:
            插值后的轨迹
        """
        raise NotImplementedError


class LinearInterpolator(BaseInterpolator):
    """线性插值器"""
    
    def interpolate(self, trajectory: List[Tuple[float, float]], 
                   missing_indices: List[int]) -> List[Tuple[float, float]]:
        """
        使用线性插值填充缺失帧
        
        Args:
            trajectory: 轨迹数据
            missing_indices: 缺失帧索引列表
            
        Returns:
            插值后的轨迹
        """
        if not missing_indices:
            return trajectory.copy()
        
        result = trajectory.copy()
        
        for missing_idx in missing_indices:
            # 寻找前后最近的有效点
            prev_point, prev_idx = self._find_previous_valid_point(trajectory, missing_idx)
            next_point, next_idx = self._find_next_valid_point(trajectory, missing_idx)
            
            if prev_point and next_point:
                # 线性插值
                ratio = (missing_idx - prev_idx) / (next_idx - prev_idx)
                interpolated = (
                    prev_point[0] + ratio * (next_point[0] - prev_point[0]),
                    prev_point[1] + ratio * (next_point[1] - prev_point[1])
                )
                result[missing_idx] = interpolated
            elif prev_point:
                # 只有前一个点，使用外推
                if self.config.get('extrapolation_enabled', True):
                    result[missing_idx] = self._extrapolate_forward(trajectory, missing_idx, prev_point, prev_idx)
            elif next_point:
                # 只有后一个点，使用外推
                if self.config.get('extrapolation_enabled', True):
                    result[missing_idx] = self._extrapolate_backward(trajectory, missing_idx, next_point, next_idx)
        
        return result
    
    def _find_previous_valid_point(self, trajectory: List[Tuple[float, float]], 
                                  missing_idx: int) -> Tuple[Optional[Tuple[float, float]], int]:
        """寻找前一个有效点"""
        for i in range(missing_idx - 1, -1, -1):
            if trajectory[i] is not None:
                return trajectory[i], i
        return None, -1
    
    def _find_next_valid_point(self, trajectory: List[Tuple[float, float]], 
                              missing_idx: int) -> Tuple[Optional[Tuple[float, float]], int]:
        """寻找后一个有效点"""
        for i in range(missing_idx + 1, len(trajectory)):
            if trajectory[i] is not None:
                return trajectory[i], i
        return None, -1
    
    def _extrapolate_forward(self, trajectory: List[Tuple[float, float]], 
                           missing_idx: int, prev_point: Tuple[float, float], 
                           prev_idx: int) -> Tuple[float, float]:
        """向前外推"""
        # 简单的线性外推
        if prev_idx > 0:
            # 寻找前前一个点来计算速度
            prev_prev_point, prev_prev_idx = self._find_previous_valid_point(trajectory, prev_idx)
            if prev_prev_point:
                # 计算速度
                dx = prev_point[0] - prev_prev_point[0]
                dy = prev_point[1] - prev_prev_point[1]
                dt = prev_idx - prev_prev_idx
                
                # 外推
                extrapolation_frames = missing_idx - prev_idx
                extrapolated = (
                    prev_point[0] + (dx / dt) * extrapolation_frames,
                    prev_point[1] + (dy / dt) * extrapolation_frames
                )
                return extrapolated
        
        # 如果没有前前一个点，直接返回前一个点
        return prev_point
    
    def _extrapolate_backward(self, trajectory: List[Tuple[float, float]], 
                            missing_idx: int, next_point: Tuple[float, float], 
                            next_idx: int) -> Tuple[float, float]:
        """向后外推"""
        # 简单的线性外推
        if next_idx < len(trajectory) - 1:
            # 寻找后后一个点来计算速度
            next_next_point, next_next_idx = self._find_next_valid_point(trajectory, next_idx)
            if next_next_point:
                # 计算速度
                dx = next_next_point[0] - next_point[0]
                dy = next_next_point[1] - next_point[1]
                dt = next_next_idx - next_idx
                
                # 外推
                extrapolation_frames = next_idx - missing_idx
                extrapolated = (
                    next_point[0] - (dx / dt) * extrapolation_frames,
                    next_point[1] - (dy / dt) * extrapolation_frames
                )
                return extrapolated
        
        # 如果没有后后一个点，直接返回后一个点
        return next_point


class CubicInterpolator(BaseInterpolator):
    """三次样条插值器"""
    
    def interpolate(self, trajectory: List[Tuple[float, float]], 
                   missing_indices: List[int]) -> List[Tuple[float, float]]:
        """
        使用三次样条插值填充缺失帧
        
        Args:
            trajectory: 轨迹数据
            missing_indices: 缺失帧索引列表
            
        Returns:
            插值后的轨迹
        """
        if not missing_indices:
            return trajectory.copy()
        
        result = trajectory.copy()
        
        # 获取所有有效点
        valid_points = []
        valid_indices = []
        for i, point in enumerate(trajectory):
            if point is not None:
                valid_points.append(point)
                valid_indices.append(i)
        
        if len(valid_points) < 2:
            return result
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 创建插值函数
        try:
            x_interp = CubicSpline(valid_indices, x_coords)
            y_interp = CubicSpline(valid_indices, y_coords)
            
            # 对缺失帧进行插值
            for missing_idx in missing_indices:
                if (self.config.get('extrapolation_enabled', True) or 
                    (min(valid_indices) <= missing_idx <= max(valid_indices))):
                    interpolated = (
                        float(x_interp(missing_idx)),
                        float(y_interp(missing_idx))
                    )
                    result[missing_idx] = interpolated
                    
        except Exception as e:
            print(f"三次样条插值失败，回退到线性插值: {e}")
            # 回退到线性插值
            linear_interpolator = LinearInterpolator(self.config)
            return linear_interpolator.interpolate(trajectory, missing_indices)
        
        return result


class SplineInterpolator(BaseInterpolator):
    """样条插值器"""
    
    def interpolate(self, trajectory: List[Tuple[float, float]], 
                   missing_indices: List[int]) -> List[Tuple[float, float]]:
        """
        使用样条插值填充缺失帧
        
        Args:
            trajectory: 轨迹数据
            missing_indices: 缺失帧索引列表
            
        Returns:
            插值后的轨迹
        """
        if not missing_indices:
            return trajectory.copy()
        
        result = trajectory.copy()
        
        # 获取所有有效点
        valid_points = []
        valid_indices = []
        for i, point in enumerate(trajectory):
            if point is not None:
                valid_points.append(point)
                valid_indices.append(i)
        
        if len(valid_points) < 2:
            return result
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 创建插值函数
        try:
            x_interp = interp1d(valid_indices, x_coords, kind='cubic', 
                              bounds_error=False, fill_value='extrapolate')
            y_interp = interp1d(valid_indices, y_coords, kind='cubic', 
                              bounds_error=False, fill_value='extrapolate')
            
            # 对缺失帧进行插值
            for missing_idx in missing_indices:
                interpolated = (
                    float(x_interp(missing_idx)),
                    float(y_interp(missing_idx))
                )
                result[missing_idx] = interpolated
                
        except Exception as e:
            print(f"样条插值失败，回退到线性插值: {e}")
            # 回退到线性插值
            linear_interpolator = LinearInterpolator(self.config)
            return linear_interpolator.interpolate(trajectory, missing_indices)
        
        return result
