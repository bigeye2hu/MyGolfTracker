#!/usr/bin/env python3
"""
真实策略实现 - 基于Club_Optimization_Algo中的实际算法
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Club_Optimization_Algo'))

from analyzer.strategy_manager import OptimizationStrategy, StrategyInfo
from typing import List, Tuple
import numpy as np

# 导入真实的算法实现
from algorithms.trajectory_optimizer import TrajectoryOptimizer as RealTrajectoryOptimizer
from algorithms.interpolation import LinearInterpolator
from algorithms.smoothing import SavitzkyGolaySmoother, GaussianSmoother
from algorithms.outlier_detection import OutlierDetector
from algorithms.physics_constraints import PhysicsConstraintValidator
from config.parameters import DEFAULT_CONFIG

def convert_trajectory_format(trajectory: List[List[float]]) -> List[Tuple[float, float]]:
    """将List[List[float]]格式转换为List[Tuple[float, float]]格式，处理无效点"""
    tuple_trajectory = []
    last_valid_point = (0.0, 0.0)
    
    for point in trajectory:
        if point is not None and len(point) >= 2:
            try:
                # 安全地转换为浮点数
                x = float(point[0])
                y = float(point[1])
                
                # 检查是否为有效坐标（不是[0,0]或包含NaN）
                if not (x == 0 and y == 0) and not (np.isnan(x) or np.isnan(y)):
                    tuple_trajectory.append((x, y))
                    last_valid_point = (x, y)  # 更新最后一个有效点
                else:
                    # 对于无效点，使用最后一个有效点
                    tuple_trajectory.append(last_valid_point)
            except (ValueError, TypeError):
                # 转换失败，使用最后一个有效点
                tuple_trajectory.append(last_valid_point)
        else:
            # 点无效，使用最后一个有效点
            tuple_trajectory.append(last_valid_point)
    
    return tuple_trajectory

def convert_back_format(trajectory: List[Tuple[float, float]]) -> List[List[float]]:
    """将List[Tuple[float, float]]格式转换回List[List[float]]格式"""
    return [[point[0] if point[0] is not None else 0.0, 
             point[1] if point[1] is not None else 0.0] for point in trajectory]

class RealSavitzkyGolayStrategy(OptimizationStrategy):
    """真实的Savitzky-Golay滤波策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="real_savitzky_golay",
            name="Savitzky-Golay滤波（真实实现）",
            description="基于Club_Optimization_Algo的真实Savitzky-Golay滤波算法",
            category="smoothing",
            parameters={
                "window_size": 5,
                "poly_order": 2
            }
        ))
        self.smoother = SavitzkyGolaySmoother(DEFAULT_CONFIG['smoothing'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 3:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        window_size = kwargs.get('window_size', self.info.parameters['window_size'])
        poly_order = kwargs.get('poly_order', self.info.parameters['poly_order'])
        
        # 更新配置
        config = DEFAULT_CONFIG['smoothing'].copy()
        config['window_size'] = window_size
        config['poly_order'] = poly_order
        
        smoother = SavitzkyGolaySmoother(config)
        smoothed = smoother.smooth(tuple_trajectory)
        
        # 转换回格式
        return convert_back_format(smoothed)

class RealLinearInterpolationStrategy(OptimizationStrategy):
    """真实的线性插值策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="real_linear_interpolation",
            name="线性插值（真实实现）",
            description="基于Club_Optimization_Algo的真实线性插值算法",
            category="interpolation",
            parameters={
                "max_gap_size": 5,
                "min_valid_points": 3
            }
        ))
        self.interpolator = LinearInterpolator(DEFAULT_CONFIG['interpolation'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 2:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        max_gap_size = kwargs.get('max_gap_size', self.info.parameters['max_gap_size'])
        min_valid_points = kwargs.get('min_valid_points', self.info.parameters['min_valid_points'])
        
        # 更新配置
        config = DEFAULT_CONFIG['interpolation'].copy()
        config['max_gap_size'] = max_gap_size
        config['min_valid_points'] = min_valid_points
        
        interpolator = LinearInterpolator(config)
        
        # 找到缺失帧
        missing_indices = []
        for i, point in enumerate(tuple_trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                missing_indices.append(i)
        
        if not missing_indices:
            return trajectory
        
        interpolated = interpolator.interpolate(tuple_trajectory, missing_indices)
        
        # 转换回格式
        return convert_back_format(interpolated)

class RealOutlierDetectionStrategy(OptimizationStrategy):
    """真实的异常值检测策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="real_outlier_detection",
            name="异常值检测（真实实现）",
            description="基于Club_Optimization_Algo的真实异常值检测算法",
            category="outlier",
            parameters={
                "z_score_threshold": 2.0,
                "distance_threshold": 0.2
            }
        ))
        self.detector = OutlierDetector(DEFAULT_CONFIG['outlier'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 3:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        z_score_threshold = kwargs.get('z_score_threshold', self.info.parameters['z_score_threshold'])
        distance_threshold = kwargs.get('distance_threshold', self.info.parameters['distance_threshold'])
        
        # 更新配置
        config = DEFAULT_CONFIG['outlier'].copy()
        config['z_score_threshold'] = z_score_threshold
        config['distance_threshold'] = distance_threshold
        
        detector = OutlierDetector(config)
        outlier_indices = detector.detect(tuple_trajectory)
        
        # 修正异常值
        result = list(tuple_trajectory)
        for idx in outlier_indices:
            if idx > 0 and idx < len(tuple_trajectory) - 1:
                # 使用前后点的平均值
                prev_point = tuple_trajectory[idx - 1]
                next_point = tuple_trajectory[idx + 1]
                if (prev_point[0] is not None and prev_point[1] is not None and 
                    next_point[0] is not None and next_point[1] is not None):
                    avg_x = (prev_point[0] + next_point[0]) / 2
                    avg_y = (prev_point[1] + next_point[1]) / 2
                    result[idx] = (avg_x, avg_y)
        
        # 转换回格式
        return convert_back_format(result)

class RealPhysicsConstraintStrategy(OptimizationStrategy):
    """真实的物理约束策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="real_physics_constraints",
            name="物理约束（真实实现）",
            description="基于Club_Optimization_Algo的真实物理约束算法",
            category="physics",
            parameters={
                "max_velocity": 0.1,
                "max_acceleration": 0.05
            }
        ))
        self.validator = PhysicsConstraintValidator(DEFAULT_CONFIG['physics'])
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 2:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        max_velocity = kwargs.get('max_velocity', self.info.parameters['max_velocity'])
        max_acceleration = kwargs.get('max_acceleration', self.info.parameters['max_acceleration'])
        
        # 更新配置
        config = DEFAULT_CONFIG['physics'].copy()
        config['max_velocity'] = max_velocity
        config['max_acceleration'] = max_acceleration
        
        validator = PhysicsConstraintValidator(config)
        validated = validator.validate(tuple_trajectory)
        
        # 转换回格式
        return convert_back_format(validated)

class RealTrajectoryOptimizationStrategy(OptimizationStrategy):
    """真实的轨迹优化策略 - 整合所有算法"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="real_trajectory_optimization",
            name="第一优化策略（真实实现）",
            description="基于Club_Optimization_Algo的完整轨迹优化算法，整合插值、平滑、异常值检测和物理约束",
            category="golf_specific",
            parameters={
                "enable_interpolation": True,
                "enable_smoothing": True,
                "enable_outlier_detection": True,
                "enable_physics_constraints": True
            }
        ))
        self.optimizer = RealTrajectoryOptimizer(DEFAULT_CONFIG)
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        if len(trajectory) < 2:
            return trajectory
        
        # 转换格式
        tuple_trajectory = convert_trajectory_format(trajectory)
        
        # 使用真实的轨迹优化器
        try:
            optimized = self.optimizer.optimize(tuple_trajectory)
            # 转换回格式
            return convert_back_format(optimized)
        except Exception as e:
            print(f"轨迹优化失败: {e}")
            return trajectory

# 注册真实策略的函数
def register_real_strategies(strategy_manager):
    """注册所有真实策略"""
    real_strategies = [
        RealSavitzkyGolayStrategy(),
        RealLinearInterpolationStrategy(),
        RealOutlierDetectionStrategy(),
        RealPhysicsConstraintStrategy(),
        RealTrajectoryOptimizationStrategy()
    ]
    
    for strategy in real_strategies:
        strategy_manager.register_strategy(strategy)
        print(f"已注册策略: {strategy.info.name} ({strategy.info.id})")
    
    print(f"已注册 {len(real_strategies)} 个真实策略")
    
    # 注册更好的策略
    try:
        from analyzer.better_strategies import register_better_strategies
        register_better_strategies(strategy_manager)
    except Exception as e:
        print(f"注册更好策略失败: {e}")
    
    # 注册智能插值策略
    try:
        from analyzer.smart_interpolation_strategy import register_smart_interpolation_strategy
        register_smart_interpolation_strategy(strategy_manager)
    except Exception as e:
        print(f"注册智能插值策略失败: {e}")
