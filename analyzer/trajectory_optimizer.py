from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import signal
from scipy.signal import savgol_filter
from .strategy_manager import get_strategy_manager
from .custom_strategies import register_custom_strategies


class TrajectoryOptimizer:
    """轨迹优化器：平滑、去噪、填补缺失数据"""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.strategy_manager = get_strategy_manager()
        # 注册真实策略
        from .real_strategies import register_real_strategies
        register_real_strategies(self.strategy_manager)
        
    def optimize_trajectory(self, 
                          raw_trajectory: List[List[float]], 
                          confidences: Optional[List[float]] = None) -> Tuple[List[List[float]], List[float]]:
        """
        优化轨迹数据
        
        Args:
            raw_trajectory: 原始轨迹 [[x, y], ...]
            confidences: 置信度列表（可选）
            
        Returns:
            (优化后的轨迹, 质量评分列表)
        """
        if len(raw_trajectory) < 3:
            return raw_trajectory, [1.0] * len(raw_trajectory)
        
        # 1. 数据预处理：分离坐标和处理缺失值
        trajectory = self._preprocess_trajectory(raw_trajectory)
        
        # 2. 异常值检测和移除
        trajectory = self._remove_outliers(trajectory)
        
        # 3. 插值填补缺失数据
        trajectory = self._interpolate_missing_data(trajectory)
        
        # 4. 平滑滤波
        trajectory = self._apply_smoothing(trajectory)
        
        # 5. 计算质量评分
        quality_scores = self._calculate_quality_scores(trajectory, raw_trajectory)
        
        return trajectory, quality_scores
    
    def optimize_with_strategy(self, 
                             raw_trajectory: List[List[float]], 
                             strategy_id: str,
                             **strategy_params) -> Tuple[List[List[float]], List[float]]:
        """
        使用指定策略优化轨迹
        
        Args:
            raw_trajectory: 原始轨迹 [[x, y], ...]
            strategy_id: 策略ID
            **strategy_params: 策略参数
            
        Returns:
            (优化后的轨迹, 质量评分列表)
        """
        if len(raw_trajectory) < 3:
            return raw_trajectory, [1.0] * len(raw_trajectory)
        
        # 预处理轨迹
        trajectory = self._preprocess_trajectory(raw_trajectory)
        
        # 转换为策略管理器需要的格式
        trajectory_tuples = []
        for point in trajectory:
            if point is not None and len(point) >= 2:
                try:
                    # 安全地转换为浮点数
                    x = float(point[0])
                    y = float(point[1])
                    
                    # 检查是否为有效坐标
                    if not (x == 0 and y == 0) and not (np.isnan(x) or np.isnan(y)):
                        trajectory_tuples.append((x, y))
                    else:
                        trajectory_tuples.append((None, None))
                except (ValueError, TypeError):
                    trajectory_tuples.append((None, None))
            else:
                trajectory_tuples.append((None, None))
        
        try:
            # 应用指定策略
            optimized_tuples = self.strategy_manager.apply_strategy(
                strategy_id, trajectory_tuples, **strategy_params
            )
            
            # 转换回列表格式
            optimized_trajectory = [[point[0], point[1]] for point in optimized_tuples]
            
            return optimized_trajectory
            
        except Exception as e:
            print(f"应用策略 {strategy_id} 时出错: {e}")
            # 回退到默认优化
            return self.optimize_trajectory(raw_trajectory)
    
    def get_available_strategies(self) -> Dict[str, Any]:
        """获取所有可用策略"""
        return self.strategy_manager.get_all_strategies()
    
    def get_strategies_by_category(self, category: str) -> Dict[str, Any]:
        """按类别获取策略"""
        return self.strategy_manager.get_strategies_by_category(category)
    
    def _preprocess_trajectory(self, raw_trajectory: List[List[float]]) -> List[List[float]]:
        """预处理轨迹数据"""
        trajectory = []
        for point in raw_trajectory:
            if len(point) >= 2:
                x, y = point[0], point[1]
                # 检查是否为有效点（非零且在合理范围内）
                if x == 0.0 and y == 0.0:
                    trajectory.append([np.nan, np.nan])
                elif 0 <= x <= 1 and 0 <= y <= 1:
                    trajectory.append([float(x), float(y)])
                else:
                    trajectory.append([np.nan, np.nan])
            else:
                trajectory.append([np.nan, np.nan])
        return trajectory
    
    def _remove_outliers(self, trajectory: List[List[float]], 
                        velocity_threshold: float = 0.3) -> List[List[float]]:
        """移除运动速度异常的点"""
        if len(trajectory) < 3:
            return trajectory
        
        # 计算相邻点之间的距离（速度代理）
        velocities = []
        for i in range(len(trajectory) - 1):
            if (not np.isnan(trajectory[i][0]) and not np.isnan(trajectory[i+1][0])):
                dx = trajectory[i+1][0] - trajectory[i][0]
                dy = trajectory[i+1][1] - trajectory[i][1]
                velocity = np.sqrt(dx*dx + dy*dy)
                velocities.append(velocity)
            else:
                velocities.append(np.nan)
        
        # 标记异常点
        cleaned_trajectory = trajectory.copy()
        for i in range(len(velocities)):
            if not np.isnan(velocities[i]) and velocities[i] > velocity_threshold:
                # 将异常点标记为 NaN
                cleaned_trajectory[i+1] = [np.nan, np.nan]
        
        return cleaned_trajectory
    
    def _interpolate_missing_data(self, trajectory: List[List[float]]) -> List[List[float]]:
        """使用线性插值填补缺失数据"""
        if len(trajectory) < 2:
            return trajectory
        
        # 分离 x 和 y 坐标
        x_coords = [point[0] for point in trajectory]
        y_coords = [point[1] for point in trajectory]
        
        # 对 x 和 y 分别进行插值
        x_interpolated = self._interpolate_1d(x_coords)
        y_interpolated = self._interpolate_1d(y_coords)
        
        # 重新组合
        interpolated_trajectory = [[x, y] for x, y in zip(x_interpolated, y_interpolated)]
        return interpolated_trajectory
    
    def _interpolate_1d(self, coords: List[float]) -> List[float]:
        """一维线性插值"""
        coords = np.array(coords)
        
        # 找到有效数据的索引
        valid_indices = ~np.isnan(coords)
        
        if not np.any(valid_indices):
            # 如果没有有效数据，返回原数组
            return coords.tolist()
        
        if np.all(valid_indices):
            # 如果没有缺失数据，直接返回
            return coords.tolist()
        
        # 线性插值
        indices = np.arange(len(coords))
        coords[~valid_indices] = np.interp(
            indices[~valid_indices],
            indices[valid_indices],
            coords[valid_indices]
        )
        
        return coords.tolist()
    
    def _apply_smoothing(self, trajectory: List[List[float]], 
                        window_length: int = 7) -> List[List[float]]:
        """应用 Savitzky-Golay 滤波器进行平滑"""
        if len(trajectory) < window_length:
            return trajectory
        
        # 确保窗口长度为奇数
        if window_length % 2 == 0:
            window_length += 1
        
        # 分离坐标
        x_coords = np.array([point[0] for point in trajectory])
        y_coords = np.array([point[1] for point in trajectory])
        
        # 检查是否有足够的有效数据点
        if len(x_coords) < window_length:
            return trajectory
        
        try:
            # 应用 Savitzky-Golay 滤波器
            x_smoothed = savgol_filter(x_coords, window_length, polyorder=2)
            y_smoothed = savgol_filter(y_coords, window_length, polyorder=2)
            
            # 重新组合
            smoothed_trajectory = [[float(x), float(y)] for x, y in zip(x_smoothed, y_smoothed)]
            return smoothed_trajectory
            
        except Exception:
            # 如果平滑失败，使用移动平均作为备选
            return self._apply_moving_average(trajectory, window_size=3)
    
    def _apply_moving_average(self, trajectory: List[List[float]], 
                            window_size: int = 3) -> List[List[float]]:
        """应用移动平均滤波器"""
        if len(trajectory) < window_size:
            return trajectory
        
        smoothed_trajectory = []
        for i in range(len(trajectory)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(trajectory), i + window_size // 2 + 1)
            
            # 计算窗口内的平均值
            x_sum = y_sum = count = 0
            for j in range(start_idx, end_idx):
                if not np.isnan(trajectory[j][0]):
                    x_sum += trajectory[j][0]
                    y_sum += trajectory[j][1]
                    count += 1
            
            if count > 0:
                smoothed_trajectory.append([x_sum / count, y_sum / count])
            else:
                smoothed_trajectory.append(trajectory[i])
        
        return smoothed_trajectory
    
    def _calculate_quality_scores(self, 
                                optimized_trajectory: List[List[float]], 
                                raw_trajectory: List[List[float]]) -> List[float]:
        """计算每个点的质量评分"""
        scores = []
        
        for i, (opt_point, raw_point) in enumerate(zip(optimized_trajectory, raw_trajectory)):
            score = 1.0
            
            # 1. 检查原始数据质量
            if raw_point == [0.0, 0.0]:
                score *= 0.3  # 原始数据缺失
            
            # 2. 检查轨迹连续性
            if i > 0 and i < len(optimized_trajectory) - 1:
                prev_point = optimized_trajectory[i-1]
                next_point = optimized_trajectory[i+1]
                
                # 计算速度变化
                v1 = np.sqrt((opt_point[0] - prev_point[0])**2 + (opt_point[1] - prev_point[1])**2)
                v2 = np.sqrt((next_point[0] - opt_point[0])**2 + (next_point[1] - opt_point[1])**2)
                
                # 速度变化过大则降低评分
                if abs(v1 - v2) > 0.1:
                    score *= 0.8
            
            scores.append(score)
        
        return scores
    
    def get_trajectory_statistics(self, trajectory: List[List[float]]) -> dict:
        """获取轨迹统计信息"""
        if not trajectory:
            return {}
        
        # 过滤有效点
        valid_points = [p for p in trajectory if not (np.isnan(p[0]) or np.isnan(p[1]))]
        
        if not valid_points:
            return {"valid_points": 0, "total_points": len(trajectory)}
        
        # 计算统计信息
        x_coords = [p[0] for p in valid_points]
        y_coords = [p[1] for p in valid_points]
        
        # 计算轨迹长度
        total_distance = 0
        for i in range(len(valid_points) - 1):
            dx = valid_points[i+1][0] - valid_points[i][0]
            dy = valid_points[i+1][1] - valid_points[i][1]
            total_distance += np.sqrt(dx*dx + dy*dy)
        
        return {
            "valid_points": len(valid_points),
            "total_points": len(trajectory),
            "coverage": len(valid_points) / len(trajectory),
            "x_range": [min(x_coords), max(x_coords)],
            "y_range": [min(y_coords), max(y_coords)],
            "total_distance": total_distance,
            "avg_velocity": total_distance / max(len(valid_points) - 1, 1)
        }
