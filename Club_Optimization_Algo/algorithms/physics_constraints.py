#!/usr/bin/env python3
"""
物理约束验证器
"""

import numpy as np
from typing import List, Tuple, Optional


class PhysicsConstraintValidator:
    """物理约束验证器"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def validate(self, trajectory: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        验证轨迹是否符合物理约束
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            验证后的轨迹
        """
        if len(trajectory) < 2:
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
        
        # 应用物理约束
        corrected_x, corrected_y = self._apply_physics_constraints(x_coords, y_coords)
        
        # 重建轨迹
        result = trajectory.copy()
        for i, (x, y) in enumerate(zip(corrected_x, corrected_y)):
            result[valid_indices[i]] = (float(x), float(y))
        
        return result
    
    def _apply_physics_constraints(self, x_coords: List[float], y_coords: List[float]) -> Tuple[List[float], List[float]]:
        """
        应用物理约束
        
        Args:
            x_coords: x坐标列表
            y_coords: y坐标列表
            
        Returns:
            修正后的x和y坐标
        """
        corrected_x = x_coords.copy()
        corrected_y = y_coords.copy()
        
        # 1. 速度约束
        corrected_x, corrected_y = self._apply_velocity_constraints(corrected_x, corrected_y)
        
        # 2. 加速度约束
        corrected_x, corrected_y = self._apply_acceleration_constraints(corrected_x, corrected_y)
        
        # 3. 重力约束
        if self.config.get('gravity_effect', True):
            corrected_x, corrected_y = self._apply_gravity_constraints(corrected_x, corrected_y)
        
        return corrected_x, corrected_y
    
    def _apply_velocity_constraints(self, x_coords: List[float], y_coords: List[float]) -> Tuple[List[float], List[float]]:
        """应用速度约束"""
        corrected_x = x_coords.copy()
        corrected_y = y_coords.copy()
        
        max_velocity = self.config.get('max_velocity', 0.1)
        min_velocity = self.config.get('min_velocity', 0.001)
        
        for i in range(1, len(corrected_x)):
            # 计算速度
            dx = corrected_x[i] - corrected_x[i-1]
            dy = corrected_y[i] - corrected_y[i-1]
            velocity = np.sqrt(dx*dx + dy*dy)
            
            # 检查速度约束
            if velocity > max_velocity:
                # 速度过大，限制速度
                scale = max_velocity / velocity
                corrected_x[i] = corrected_x[i-1] + dx * scale
                corrected_y[i] = corrected_y[i-1] + dy * scale
            elif velocity < min_velocity and velocity > 0:
                # 速度过小，增加最小速度
                scale = min_velocity / velocity
                corrected_x[i] = corrected_x[i-1] + dx * scale
                corrected_y[i] = corrected_y[i-1] + dy * scale
        
        return corrected_x, corrected_y
    
    def _apply_acceleration_constraints(self, x_coords: List[float], y_coords: List[float]) -> Tuple[List[float], List[float]]:
        """应用加速度约束"""
        corrected_x = x_coords.copy()
        corrected_y = y_coords.copy()
        
        max_acceleration = self.config.get('max_acceleration', 0.05)
        
        for i in range(2, len(corrected_x)):
            # 计算加速度
            dx1 = corrected_x[i-1] - corrected_x[i-2]
            dy1 = corrected_y[i-1] - corrected_y[i-2]
            dx2 = corrected_x[i] - corrected_x[i-1]
            dy2 = corrected_y[i] - corrected_y[i-1]
            
            acc_x = dx2 - dx1
            acc_y = dy2 - dy1
            acceleration = np.sqrt(acc_x*acc_x + acc_y*acc_y)
            
            # 检查加速度约束
            if acceleration > max_acceleration:
                # 加速度过大，限制加速度
                scale = max_acceleration / acceleration
                corrected_x[i] = corrected_x[i-1] + (dx1 + acc_x * scale)
                corrected_y[i] = corrected_y[i-1] + (dy1 + acc_y * scale)
        
        return corrected_x, corrected_y
    
    def _apply_gravity_constraints(self, x_coords: List[float], y_coords: List[float]) -> Tuple[List[float], List[float]]:
        """应用重力约束"""
        corrected_x = x_coords.copy()
        corrected_y = y_coords.copy()
        
        gravity_constant = self.config.get('gravity_constant', 0.001)
        
        for i in range(1, len(corrected_y)):
            # 重力影响y坐标（向下为正）
            gravity_effect = gravity_constant * i  # 随时间累积
            corrected_y[i] += gravity_effect
        
        return corrected_x, corrected_y
    
    def get_physics_statistics(self, trajectory: List[Tuple[float, float]]) -> dict:
        """
        获取物理统计信息
        
        Args:
            trajectory: 轨迹数据
            
        Returns:
            物理统计信息
        """
        # 获取有效点
        valid_points = []
        for point in trajectory:
            if point is not None:
                valid_points.append(point)
        
        if len(valid_points) < 2:
            return {
                'total_points': len(trajectory),
                'valid_points': len(valid_points),
                'max_velocity': 0.0,
                'avg_velocity': 0.0,
                'max_acceleration': 0.0,
                'avg_acceleration': 0.0,
                'velocity_violations': 0,
                'acceleration_violations': 0
            }
        
        # 分离x和y坐标
        x_coords = [point[0] for point in valid_points]
        y_coords = [point[1] for point in valid_points]
        
        # 计算速度
        velocities = []
        for i in range(1, len(x_coords)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            velocity = np.sqrt(dx*dx + dy*dy)
            velocities.append(velocity)
        
        # 计算加速度
        accelerations = []
        for i in range(1, len(velocities)):
            acceleration = velocities[i] - velocities[i-1]
            accelerations.append(acceleration)
        
        # 统计信息
        max_velocity = max(velocities) if velocities else 0.0
        avg_velocity = np.mean(velocities) if velocities else 0.0
        max_acceleration = max(accelerations) if accelerations else 0.0
        avg_acceleration = np.mean(accelerations) if accelerations else 0.0
        
        # 检查约束违反
        max_velocity_limit = self.config.get('max_velocity', 0.1)
        max_acceleration_limit = self.config.get('max_acceleration', 0.05)
        
        velocity_violations = sum(1 for v in velocities if v > max_velocity_limit)
        acceleration_violations = sum(1 for a in accelerations if a > max_acceleration_limit)
        
        return {
            'total_points': len(trajectory),
            'valid_points': len(valid_points),
            'max_velocity': max_velocity,
            'avg_velocity': avg_velocity,
            'max_acceleration': max_acceleration,
            'avg_acceleration': avg_acceleration,
            'velocity_violations': velocity_violations,
            'acceleration_violations': acceleration_violations,
            'velocity_violation_rate': velocity_violations / len(velocities) if velocities else 0.0,
            'acceleration_violation_rate': acceleration_violations / len(accelerations) if accelerations else 0.0
        }
