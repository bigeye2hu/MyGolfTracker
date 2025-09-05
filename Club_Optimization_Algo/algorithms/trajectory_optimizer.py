#!/usr/bin/env python3
"""
轨迹优化主控制器
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from .interpolation import LinearInterpolator
from .smoothing import SavitzkyGolaySmoother
from .outlier_detection import OutlierDetector
from .physics_constraints import PhysicsConstraintValidator
from config.parameters import DEFAULT_CONFIG


class TrajectoryOptimizer:
    """
    轨迹优化主控制器
    
    整合多种算法来优化高尔夫杆头轨迹：
    1. 缺失帧插值
    2. 轨迹平滑
    3. 异常值检测和修正
    4. 物理约束验证
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化轨迹优化器
        
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        self.config = config or DEFAULT_CONFIG
        
        # 初始化各个算法模块
        self.interpolator = LinearInterpolator(
            self.config['interpolation']
        )
        self.smoother = SavitzkyGolaySmoother(
            self.config['smoothing']
        )
        self.outlier_detector = OutlierDetector(
            self.config['outlier']
        )
        self.physics_validator = PhysicsConstraintValidator(
            self.config['physics']
        )
        
        # 统计信息
        self.stats = {
            'original_frames': 0,
            'missing_frames': 0,
            'interpolated_frames': 0,
            'outliers_removed': 0,
            'processing_time': 0.0,
            'detection_rate': 0.0,
        }
    
    def optimize(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        优化轨迹
        
        Args:
            trajectory: 原始轨迹点列表，格式为[(x1,y1), (x2,y2), ...]
                       缺失帧用None或(0,0)表示
            
        Returns:
            优化后的轨迹点列表
        """
        import time
        start_time = time.time()
        
        # 1. 数据预处理
        processed_trajectory = self._preprocess_trajectory(trajectory)
        
        # 2. 缺失帧检测
        missing_indices = self._detect_missing_frames(processed_trajectory)
        
        # 3. 插值填充
        if missing_indices:
            interpolated_trajectory = self.interpolator.interpolate(
                processed_trajectory, missing_indices
            )
        else:
            interpolated_trajectory = processed_trajectory.copy()
        
        # 4. 异常值检测和修正
        outlier_indices = self.outlier_detector.detect(interpolated_trajectory)
        if outlier_indices:
            interpolated_trajectory = self._correct_outliers(
                interpolated_trajectory, outlier_indices
            )
        
        # 5. 轨迹平滑
        smoothed_trajectory = self.smoother.smooth(interpolated_trajectory)
        
        # 6. 物理约束验证
        validated_trajectory = self.physics_validator.validate(smoothed_trajectory)
        
        # 7. 更新统计信息
        self._update_stats(trajectory, missing_indices, outlier_indices, start_time)
        
        return validated_trajectory
    
    def _preprocess_trajectory(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        预处理轨迹数据
        
        Args:
            trajectory: 原始轨迹
            
        Returns:
            预处理后的轨迹
        """
        processed = []
        for point in trajectory:
            if point is None or point == (0, 0) or point == [0, 0]:
                processed.append(None)
            else:
                # 确保点是元组格式
                if isinstance(point, list):
                    processed.append(tuple(point))
                else:
                    processed.append(point)
        
        return processed
    
    def _detect_missing_frames(self, trajectory: List[Tuple[float, float]]) -> List[int]:
        """
        检测缺失帧
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            缺失帧索引列表
        """
        missing_indices = []
        for i, point in enumerate(trajectory):
            if point is None:
                missing_indices.append(i)
        
        return missing_indices
    
    def _correct_outliers(self, trajectory: List[Tuple[float, float]], 
                         outlier_indices: List[int]) -> List[Tuple[float, float]]:
        """
        修正异常值
        
        Args:
            trajectory: 轨迹数据
            outlier_indices: 异常值索引列表
            
        Returns:
            修正后的轨迹
        """
        corrected_trajectory = trajectory.copy()
        
        for idx in outlier_indices:
            # 使用周围有效点进行插值修正
            corrected_point = self._interpolate_outlier(trajectory, idx)
            if corrected_point:
                corrected_trajectory[idx] = corrected_point
        
        return corrected_trajectory
    
    def _interpolate_outlier(self, trajectory: List[Tuple[float, float]], 
                           outlier_idx: int) -> Optional[Tuple[float, float]]:
        """
        插值修正单个异常值
        
        Args:
            trajectory: 轨迹数据
            outlier_idx: 异常值索引
            
        Returns:
            修正后的点坐标
        """
        # 寻找前后最近的有效点
        prev_idx = None
        next_idx = None
        
        # 向前搜索
        for i in range(outlier_idx - 1, -1, -1):
            if trajectory[i] is not None:
                prev_idx = i
                break
        
        # 向后搜索
        for i in range(outlier_idx + 1, len(trajectory)):
            if trajectory[i] is not None:
                next_idx = i
                break
        
        # 如果找到前后点，进行线性插值
        if prev_idx is not None and next_idx is not None:
            prev_point = trajectory[prev_idx]
            next_point = trajectory[next_idx]
            
            ratio = (outlier_idx - prev_idx) / (next_idx - prev_idx)
            interpolated = (
                prev_point[0] + ratio * (next_point[0] - prev_point[0]),
                prev_point[1] + ratio * (next_point[1] - prev_point[1])
            )
            return interpolated
        
        return None
    
    def _update_stats(self, original_trajectory: List[Tuple[float, float]], 
                     missing_indices: List[int], outlier_indices: List[int], 
                     start_time: float):
        """
        更新统计信息
        
        Args:
            original_trajectory: 原始轨迹
            missing_indices: 缺失帧索引
            outlier_indices: 异常值索引
            start_time: 开始时间
        """
        import time
        
        self.stats['original_frames'] = len(original_trajectory)
        self.stats['missing_frames'] = len(missing_indices)
        self.stats['interpolated_frames'] = len(missing_indices)
        self.stats['outliers_removed'] = len(outlier_indices)
        self.stats['processing_time'] = time.time() - start_time
        self.stats['detection_rate'] = (len(original_trajectory) - len(missing_indices)) / len(original_trajectory)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return self.stats.copy()
    
    def get_optimization_report(self) -> str:
        """
        获取优化报告
        
        Returns:
            优化报告字符串
        """
        stats = self.stats
        report = f"""
轨迹优化报告
============
原始帧数: {stats['original_frames']}
缺失帧数: {stats['missing_frames']}
插值帧数: {stats['interpolated_frames']}
异常值修正: {stats['outliers_removed']}
处理时间: {stats['processing_time']:.3f}秒
检测率: {stats['detection_rate']:.2%}
优化后检测率: {((stats['original_frames'] - stats['missing_frames'] + stats['interpolated_frames']) / stats['original_frames']):.2%}
        """
        return report.strip()
