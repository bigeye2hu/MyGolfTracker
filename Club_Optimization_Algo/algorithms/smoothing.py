#!/usr/bin/env python3
"""
轨迹平滑算法
"""

import numpy as np
from typing import List, Tuple
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d


class BaseSmoother:
    """平滑算法基类"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def smooth(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        平滑轨迹
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            平滑后的轨迹
        """
        raise NotImplementedError


class SavitzkyGolaySmoother(BaseSmoother):
    """Savitzky-Golay滤波器"""
    
    def smooth(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        使用Savitzky-Golay滤波器平滑轨迹
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            平滑后的轨迹
        """
        if len(trajectory) < 3:
            return trajectory.copy()
        
        # 分离x和y坐标
        x_coords = []
        y_coords = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                x_coords.append(point[0])
                y_coords.append(point[1])
                valid_indices.append(i)
        
        if len(x_coords) < 3:
            return trajectory.copy()
        
        # 获取配置参数
        window_size = min(self.config.get('window_size', 5), len(x_coords))
        poly_order = min(self.config.get('poly_order', 2), window_size - 1)
        
        # 确保窗口大小为奇数
        if window_size % 2 == 0:
            window_size -= 1
        
        # 确保多项式阶数小于窗口大小
        if poly_order >= window_size:
            poly_order = window_size - 1
        
        try:
            # 应用Savitzky-Golay滤波器
            smooth_x = savgol_filter(x_coords, window_size, poly_order)
            smooth_y = savgol_filter(y_coords, window_size, poly_order)
            
            # 重建轨迹
            result = trajectory.copy()
            for i, (x, y) in enumerate(zip(smooth_x, smooth_y)):
                result[valid_indices[i]] = (float(x), float(y))
            
            return result
            
        except Exception as e:
            print(f"Savitzky-Golay滤波失败: {e}")
            return trajectory.copy()


class GaussianSmoother(BaseSmoother):
    """高斯滤波器"""
    
    def smooth(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        使用高斯滤波器平滑轨迹
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            平滑后的轨迹
        """
        if len(trajectory) < 3:
            return trajectory.copy()
        
        # 分离x和y坐标
        x_coords = []
        y_coords = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                x_coords.append(point[0])
                y_coords.append(point[1])
                valid_indices.append(i)
        
        if len(x_coords) < 3:
            return trajectory.copy()
        
        # 获取配置参数
        sigma = self.config.get('sigma', 1.0)
        
        try:
            # 应用高斯滤波器
            smooth_x = gaussian_filter1d(x_coords, sigma=sigma)
            smooth_y = gaussian_filter1d(y_coords, sigma=sigma)
            
            # 重建轨迹
            result = trajectory.copy()
            for i, (x, y) in enumerate(zip(smooth_x, smooth_y)):
                result[valid_indices[i]] = (float(x), float(y))
            
            return result
            
        except Exception as e:
            print(f"高斯滤波失败: {e}")
            return trajectory.copy()


class MovingAverageSmoother(BaseSmoother):
    """移动平均滤波器"""
    
    def smooth(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        使用移动平均滤波器平滑轨迹
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            平滑后的轨迹
        """
        if len(trajectory) < 3:
            return trajectory.copy()
        
        # 分离x和y坐标
        x_coords = []
        y_coords = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                x_coords.append(point[0])
                y_coords.append(point[1])
                valid_indices.append(i)
        
        if len(x_coords) < 3:
            return trajectory.copy()
        
        # 获取配置参数
        window_size = min(self.config.get('window_size', 5), len(x_coords))
        
        # 确保窗口大小为奇数
        if window_size % 2 == 0:
            window_size -= 1
        
        try:
            # 应用移动平均滤波器
            smooth_x = self._moving_average(x_coords, window_size)
            smooth_y = self._moving_average(y_coords, window_size)
            
            # 重建轨迹
            result = trajectory.copy()
            for i, (x, y) in enumerate(zip(smooth_x, smooth_y)):
                result[valid_indices[i]] = (float(x), float(y))
            
            return result
            
        except Exception as e:
            print(f"移动平均滤波失败: {e}")
            return trajectory.copy()
    
    def _moving_average(self, data: List[float], window_size: int) -> List[float]:
        """计算移动平均"""
        if len(data) < window_size:
            return data.copy()
        
        result = []
        half_window = window_size // 2
        
        for i in range(len(data)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(data), i + half_window + 1)
            
            window_data = data[start_idx:end_idx]
            result.append(sum(window_data) / len(window_data))
        
        return result


class AdaptiveSmoother(BaseSmoother):
    """自适应平滑器"""
    
    def smooth(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        使用自适应平滑算法
        
        根据轨迹的局部特征选择不同的平滑策略
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            平滑后的轨迹
        """
        if len(trajectory) < 3:
            return trajectory.copy()
        
        # 分离x和y坐标
        x_coords = []
        y_coords = []
        valid_indices = []
        
        for i, point in enumerate(trajectory):
            if point is not None:
                x_coords.append(point[0])
                y_coords.append(point[1])
                valid_indices.append(i)
        
        if len(x_coords) < 3:
            return trajectory.copy()
        
        # 计算轨迹的局部特征
        velocities = self._calculate_velocities(x_coords, y_coords)
        accelerations = self._calculate_accelerations(velocities)
        
        # 根据特征选择平滑策略
        smooth_x = []
        smooth_y = []
        
        for i in range(len(x_coords)):
            # 根据速度和加速度选择平滑参数
            if i < len(velocities) and abs(velocities[i]) > 0.05:  # 高速区域
                # 使用较小的平滑窗口
                window_size = 3
            elif i < len(accelerations) and abs(accelerations[i]) > 0.02:  # 高加速度区域
                # 使用中等平滑窗口
                window_size = 5
            else:  # 低速区域
                # 使用较大的平滑窗口
                window_size = 7
            
            # 应用局部平滑
            local_x = self._local_smooth(x_coords, i, window_size)
            local_y = self._local_smooth(y_coords, i, window_size)
            
            smooth_x.append(local_x)
            smooth_y.append(local_y)
        
        # 重建轨迹
        result = trajectory.copy()
        for i, (x, y) in enumerate(zip(smooth_x, smooth_y)):
            result[valid_indices[i]] = (float(x), float(y))
        
        return result
    
    def _calculate_velocities(self, x_coords: List[float], y_coords: List[float]) -> List[float]:
        """计算速度"""
        velocities = []
        for i in range(1, len(x_coords)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            velocity = np.sqrt(dx*dx + dy*dy)
            velocities.append(velocity)
        return velocities
    
    def _calculate_accelerations(self, velocities: List[float]) -> List[float]:
        """计算加速度"""
        accelerations = []
        for i in range(1, len(velocities)):
            acceleration = velocities[i] - velocities[i-1]
            accelerations.append(acceleration)
        return accelerations
    
    def _local_smooth(self, data: List[float], center_idx: int, window_size: int) -> float:
        """局部平滑"""
        half_window = window_size // 2
        start_idx = max(0, center_idx - half_window)
        end_idx = min(len(data), center_idx + half_window + 1)
        
        window_data = data[start_idx:end_idx]
        return sum(window_data) / len(window_data)
