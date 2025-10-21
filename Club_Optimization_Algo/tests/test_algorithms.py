#!/usr/bin/env python3
"""
算法测试文件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import numpy as np
from algorithms.trajectory_optimizer import TrajectoryOptimizer
from algorithms.interpolation import LinearInterpolator, CubicInterpolator
from algorithms.smoothing import SavitzkyGolaySmoother, GaussianSmoother
from algorithms.outlier_detection import OutlierDetector
from algorithms.physics_constraints import PhysicsConstraintValidator
from config.parameters import DEFAULT_CONFIG


class TestTrajectoryOptimizer(unittest.TestCase):
    """轨迹优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.optimizer = TrajectoryOptimizer(DEFAULT_CONFIG)
        
        # 创建测试轨迹
        self.test_trajectory = [
            (0.1, 0.1), (0.2, 0.2), None, (0.4, 0.4), (0.5, 0.5),
            None, None, (0.8, 0.8), (0.9, 0.9), (1.0, 1.0)
        ]
    
    def test_optimize(self):
        """测试轨迹优化"""
        result = self.optimizer.optimize(self.test_trajectory)
        
        # 检查结果长度
        self.assertEqual(len(result), len(self.test_trajectory))
        
        # 检查所有点都不为None
        for point in result:
            self.assertIsNotNone(point)
        
        # 检查统计信息
        stats = self.optimizer.get_stats()
        self.assertGreater(stats['detection_rate'], 0.0)
    
    def test_empty_trajectory(self):
        """测试空轨迹"""
        result = self.optimizer.optimize([])
        self.assertEqual(len(result), 0)
    
    def test_single_point(self):
        """测试单点轨迹"""
        result = self.optimizer.optimize([(0.5, 0.5)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0.5, 0.5))


class TestInterpolation(unittest.TestCase):
    """插值算法测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_CONFIG['interpolation']
        self.linear_interpolator = LinearInterpolator(self.config)
        self.cubic_interpolator = CubicInterpolator(self.config)
        
        # 创建测试轨迹
        self.test_trajectory = [
            (0.1, 0.1), (0.2, 0.2), None, (0.4, 0.4), (0.5, 0.5)
        ]
        self.missing_indices = [2]
    
    def test_linear_interpolation(self):
        """测试线性插值"""
        result = self.linear_interpolator.interpolate(self.test_trajectory, self.missing_indices)
        
        # 检查缺失帧是否被填充
        self.assertIsNotNone(result[2])
        
        # 检查插值点是否在合理范围内
        self.assertGreaterEqual(result[2][0], 0.1)
        self.assertLessEqual(result[2][0], 0.4)
        self.assertGreaterEqual(result[2][1], 0.1)
        self.assertLessEqual(result[2][1], 0.4)
    
    def test_cubic_interpolation(self):
        """测试三次样条插值"""
        result = self.cubic_interpolator.interpolate(self.test_trajectory, self.missing_indices)
        
        # 检查缺失帧是否被填充
        self.assertIsNotNone(result[2])
        
        # 检查插值点是否在合理范围内
        self.assertGreaterEqual(result[2][0], 0.1)
        self.assertLessEqual(result[2][0], 0.4)
        self.assertGreaterEqual(result[2][1], 0.1)
        self.assertLessEqual(result[2][1], 0.4)


class TestSmoothing(unittest.TestCase):
    """平滑算法测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_CONFIG['smoothing']
        self.savgol_smoother = SavitzkyGolaySmoother(self.config)
        self.gaussian_smoother = GaussianSmoother(self.config)
        
        # 创建测试轨迹
        self.test_trajectory = [
            (0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4), (0.5, 0.5)
        ]
    
    def test_savgol_smoothing(self):
        """测试Savitzky-Golay平滑"""
        result = self.savgol_smoother.smooth(self.test_trajectory)
        
        # 检查结果长度
        self.assertEqual(len(result), len(self.test_trajectory))
        
        # 检查所有点都不为None
        for point in result:
            self.assertIsNotNone(point)
    
    def test_gaussian_smoothing(self):
        """测试高斯平滑"""
        result = self.gaussian_smoother.smooth(self.test_trajectory)
        
        # 检查结果长度
        self.assertEqual(len(result), len(self.test_trajectory))
        
        # 检查所有点都不为None
        for point in result:
            self.assertIsNotNone(point)


class TestOutlierDetection(unittest.TestCase):
    """异常值检测测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_CONFIG['outlier']
        self.detector = OutlierDetector(self.config)
        
        # 创建测试轨迹（包含异常值）
        self.test_trajectory = [
            (0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (10.0, 10.0), (0.5, 0.5)  # (10.0, 10.0)是异常值
        ]
    
    def test_outlier_detection(self):
        """测试异常值检测"""
        outliers = self.detector.detect(self.test_trajectory)
        
        # 检查是否检测到异常值
        self.assertGreater(len(outliers), 0)
        
        # 检查异常值索引是否正确
        self.assertIn(3, outliers)  # 索引3是异常值
    
    def test_outlier_statistics(self):
        """测试异常值统计"""
        stats = self.detector.get_outlier_statistics(self.test_trajectory)
        
        # 检查统计信息
        self.assertGreater(stats['outliers'], 0)
        self.assertGreater(stats['outlier_rate'], 0.0)


class TestPhysicsConstraints(unittest.TestCase):
    """物理约束测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_CONFIG['physics']
        self.validator = PhysicsConstraintValidator(self.config)
        
        # 创建测试轨迹
        self.test_trajectory = [
            (0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4), (0.5, 0.5)
        ]
    
    def test_physics_validation(self):
        """测试物理约束验证"""
        result = self.validator.validate(self.test_trajectory)
        
        # 检查结果长度
        self.assertEqual(len(result), len(self.test_trajectory))
        
        # 检查所有点都不为None
        for point in result:
            self.assertIsNotNone(point)
    
    def test_physics_statistics(self):
        """测试物理统计"""
        stats = self.validator.get_physics_statistics(self.test_trajectory)
        
        # 检查统计信息
        self.assertGreaterEqual(stats['max_velocity'], 0.0)
        self.assertGreaterEqual(stats['avg_velocity'], 0.0)
        self.assertGreaterEqual(stats['max_acceleration'], 0.0)
        self.assertGreaterEqual(stats['avg_acceleration'], 0.0)


if __name__ == '__main__':
    # 运行测试
    unittest.main()
