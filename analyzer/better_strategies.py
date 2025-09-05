#!/usr/bin/env python3
"""
更好的优化策略 - 只处理缺失帧，不调整已检测的位置
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from analyzer.strategy_manager import OptimizationStrategy, StrategyInfo
from analyzer.real_strategies import convert_trajectory_format, convert_back_format
from Club_Optimization_Algo.algorithms.interpolation import LinearInterpolator
from config.parameters import DEFAULT_CONFIG

class ConservativeInterpolationStrategy(OptimizationStrategy):
    """保守插值策略 - 只对缺失帧进行插值，不调整已检测的位置"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="conservative_interpolation",
            name="保守插值策略",
            description="只对缺失帧进行插值，保持已检测的杆头位置不变",
            category="conservative",
            parameters={
                "max_gap_size": 5,
                "min_valid_points": 2
            }
        ))
        self.interpolator = LinearInterpolator(DEFAULT_CONFIG['interpolation'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 2:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        # 检测缺失帧（用(0,0)表示）
        missing_indices = []
        for i, point in enumerate(tuple_trajectory):
            if point == (0.0, 0.0):
                missing_indices.append(i)
        
        # 如果没有缺失帧，直接返回原轨迹
        if not missing_indices:
            return trajectory
        
        # 只对缺失帧进行插值
        try:
            interpolated = self.interpolator.interpolate(tuple_trajectory, missing_indices)
            return convert_back_format(interpolated)
        except Exception as e:
            print(f"保守插值失败: {e}")
            # 如果插值失败，至少保持原轨迹不变
            return trajectory

class OutlierOnlyStrategy(OptimizationStrategy):
    """异常值修正策略 - 只修正明显的异常值，不调整正常检测"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="outlier_only",
            name="异常值修正策略",
            description="只修正明显的异常值，保持正常检测的位置不变",
            category="conservative",
            parameters={
                "z_score_threshold": 3.0,  # 更严格的阈值
                "distance_threshold": 0.3,  # 更大的距离阈值
                "velocity_threshold": 0.2   # 更大的速度阈值
            }
        ))
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 3:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        # 检测异常值
        outlier_indices = self._detect_outliers(tuple_trajectory)
        
        # 只修正异常值
        if outlier_indices:
            corrected = self._correct_outliers(tuple_trajectory, outlier_indices)
            return convert_back_format(corrected)
        else:
            return trajectory
    
    def _detect_outliers(self, trajectory: List[Tuple[float, float]]) -> List[int]:
        """检测异常值"""
        if len(trajectory) < 3:
            return []
        
        outliers = []
        
        for i in range(1, len(trajectory) - 1):
            prev_point = trajectory[i-1]
            curr_point = trajectory[i]
            next_point = trajectory[i+1]
            
            # 跳过(0,0)点
            if curr_point == (0.0, 0.0) or prev_point == (0.0, 0.0) or next_point == (0.0, 0.0):
                continue
            
            # 计算速度
            v1 = self._calculate_velocity(prev_point, curr_point)
            v2 = self._calculate_velocity(curr_point, next_point)
            
            # 计算加速度
            acceleration = abs(v2 - v1)
            
            # 如果加速度过大，认为是异常值
            if acceleration > 0.2:  # 可调参数
                outliers.append(i)
        
        return outliers
    
    def _calculate_velocity(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间的速度"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return np.sqrt(dx*dx + dy*dy)
    
    def _correct_outliers(self, trajectory: List[Tuple[float, float]], outlier_indices: List[int]) -> List[Tuple[float, float]]:
        """修正异常值"""
        corrected = trajectory.copy()
        
        for idx in outlier_indices:
            # 使用前后点的平均值
            if idx > 0 and idx < len(trajectory) - 1:
                prev_point = trajectory[idx-1]
                next_point = trajectory[idx+1]
                
                if prev_point != (0.0, 0.0) and next_point != (0.0, 0.0):
                    avg_x = (prev_point[0] + next_point[0]) / 2
                    avg_y = (prev_point[1] + next_point[1]) / 2
                    corrected[idx] = (avg_x, avg_y)
        
        return corrected

class MinimalProcessingStrategy(OptimizationStrategy):
    """最小处理策略 - 只做最基本的处理"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="minimal_processing",
            name="最小处理策略",
            description="只做最基本的处理：插值缺失帧，修正明显异常值",
            category="conservative",
            parameters={
                "max_gap_size": 3,
                "outlier_threshold": 0.3
            }
        ))
        self.interpolator = LinearInterpolator(DEFAULT_CONFIG['interpolation'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 2:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        # 1. 检测缺失帧
        missing_indices = []
        for i, point in enumerate(tuple_trajectory):
            if point == (0.0, 0.0):
                missing_indices.append(i)
        
        # 2. 插值缺失帧
        if missing_indices:
            try:
                interpolated = self.interpolator.interpolate(tuple_trajectory, missing_indices)
            except Exception as e:
                print(f"插值失败: {e}")
                interpolated = tuple_trajectory
        else:
            interpolated = tuple_trajectory
        
        # 3. 检测并修正明显异常值
        corrected = self._correct_obvious_outliers(interpolated)
        
        return convert_back_format(corrected)
    
    def _correct_obvious_outliers(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """修正明显的异常值"""
        if len(trajectory) < 3:
            return trajectory
        
        corrected = trajectory.copy()
        
        for i in range(1, len(trajectory) - 1):
            prev_point = trajectory[i-1]
            curr_point = trajectory[i]
            next_point = trajectory[i+1]
            
            # 跳过(0,0)点
            if curr_point == (0.0, 0.0) or prev_point == (0.0, 0.0) or next_point == (0.0, 0.0):
                continue
            
            # 计算距离
            dist_prev = self._calculate_distance(prev_point, curr_point)
            dist_next = self._calculate_distance(curr_point, next_point)
            
            # 如果距离过大，认为是异常值
            if dist_prev > 0.3 or dist_next > 0.3:  # 可调参数
                # 使用前后点的平均值
                avg_x = (prev_point[0] + next_point[0]) / 2
                avg_y = (prev_point[1] + next_point[1]) / 2
                corrected[i] = (avg_x, avg_y)
        
        return corrected
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间的距离"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return np.sqrt(dx*dx + dy*dy)

# 注册更好的策略
def register_better_strategies(strategy_manager):
    """注册更好的策略"""
    better_strategies = [
        ConservativeInterpolationStrategy(),
        OutlierOnlyStrategy(),
        MinimalProcessingStrategy()
    ]
    
    for strategy in better_strategies:
        strategy_manager.register_strategy(strategy)
        print(f"已注册策略: {strategy.info.name} ({strategy.info.id})")
    
    print(f"已注册 {len(better_strategies)} 个更好的策略")
