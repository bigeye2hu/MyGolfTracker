#!/usr/bin/env python3
"""
策略管理库 - 用于管理不同的轨迹优化策略
"""

from typing import Dict, List, Tuple, Any, Callable
import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class StrategyInfo:
    """策略信息"""
    id: str
    name: str
    description: str
    category: str
    parameters: Dict[str, Any] = None

class OptimizationStrategy(ABC):
    """优化策略基类"""
    
    def __init__(self, strategy_info: StrategyInfo):
        self.info = strategy_info
    
    @abstractmethod
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        """优化轨迹数据"""
        pass
    
    def get_info(self) -> StrategyInfo:
        """获取策略信息"""
        return self.info

class SavitzkyGolayStrategy(OptimizationStrategy):
    """Savitzky-Golay滤波策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="savitzky_golay",
            name="Savitzky-Golay滤波",
            description="使用Savitzky-Golay滤波器平滑轨迹，保持峰值特征",
            category="smoothing",
            parameters={
                "window_length": 5,
                "polyorder": 2
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        window_length = kwargs.get('window_length', self.info.parameters['window_length'])
        polyorder = kwargs.get('polyorder', self.info.parameters['polyorder'])
        
        # 确保窗口长度不超过数据长度
        window_length = min(window_length, len(trajectory))
        if window_length % 2 == 0:
            window_length -= 1
        
        try:
            from scipy.signal import savgol_filter
            
            x_coords = [point[0] for point in trajectory]
            y_coords = [point[1] for point in trajectory]
            
            # 处理无效值
            x_coords = [x if x is not None and not np.isnan(x) else 0 for x in x_coords]
            y_coords = [y if y is not None and not np.isnan(y) else 0 for y in y_coords]
            
            if len(x_coords) >= window_length:
                x_smooth = savgol_filter(x_coords, window_length, polyorder)
                y_smooth = savgol_filter(y_coords, window_length, polyorder)
                
                return list(zip(x_smooth, y_smooth))
            else:
                return trajectory
                
        except ImportError:
            # 如果没有scipy，使用简单的移动平均
            return self._simple_smoothing(trajectory, window_length)
    
    def _simple_smoothing(self, trajectory: List[Tuple[float, float]], window: int) -> List[Tuple[float, float]]:
        """简单的移动平均平滑"""
        if len(trajectory) <= window:
            return trajectory
        
        result = []
        for i in range(len(trajectory)):
            start = max(0, i - window // 2)
            end = min(len(trajectory), i + window // 2 + 1)
            
            window_data = trajectory[start:end]
            valid_points = [p for p in window_data if p[0] is not None and p[1] is not None]
            
            if valid_points:
                avg_x = sum(p[0] for p in valid_points) / len(valid_points)
                avg_y = sum(p[1] for p in valid_points) / len(valid_points)
                result.append((avg_x, avg_y))
            else:
                result.append(trajectory[i])
        
        return result

class KalmanFilterStrategy(OptimizationStrategy):
    """卡尔曼滤波策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="kalman_filter",
            name="卡尔曼滤波",
            description="使用卡尔曼滤波器进行轨迹预测和平滑",
            category="prediction",
            parameters={
                "process_noise": 0.1,
                "measurement_noise": 0.5
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 2:
            return trajectory
        
        process_noise = kwargs.get('process_noise', self.info.parameters['process_noise'])
        measurement_noise = kwargs.get('measurement_noise', self.info.parameters['measurement_noise'])
        
        # 简化的卡尔曼滤波实现
        result = []
        x, y = trajectory[0]
        vx, vy = 0, 0
        
        for i, (mx, my) in enumerate(trajectory):
            if mx is None or my is None or np.isnan(mx) or np.isnan(my):
                result.append((x, y))
                continue
            
            # 预测步骤
            x_pred = x + vx
            y_pred = y + vy
            
            # 更新步骤
            k = process_noise / (process_noise + measurement_noise)
            x = x_pred + k * (mx - x_pred)
            y = y_pred + k * (my - y_pred)
            
            # 更新速度
            if i > 0:
                vx = x - result[-1][0]
                vy = y - result[-1][1]
            
            result.append((x, y))
        
        return result

class LinearInterpolationStrategy(OptimizationStrategy):
    """线性插值策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="linear_interpolation",
            name="线性插值",
            description="对缺失点进行线性插值填充",
            category="interpolation",
            parameters={
                "max_gap": 5
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 2:
            return trajectory
        
        max_gap = kwargs.get('max_gap', self.info.parameters['max_gap'])
        result = []
        
        for i, point in enumerate(trajectory):
            if point[0] is not None and point[1] is not None and not np.isnan(point[0]) and not np.isnan(point[1]):
                result.append(point)
            else:
                # 寻找前后有效点进行插值
                prev_valid = None
                next_valid = None
                
                # 向前查找
                for j in range(i-1, -1, -1):
                    if (trajectory[j][0] is not None and trajectory[j][1] is not None and 
                        not np.isnan(trajectory[j][0]) and not np.isnan(trajectory[j][1])):
                        prev_valid = trajectory[j]
                        break
                
                # 向后查找
                for j in range(i+1, len(trajectory)):
                    if (trajectory[j][0] is not None and trajectory[j][1] is not None and 
                        not np.isnan(trajectory[j][0]) and not np.isnan(trajectory[j][1])):
                        next_valid = trajectory[j]
                        break
                
                if prev_valid and next_valid:
                    # 线性插值
                    gap = next_valid[0] - prev_valid[0] if next_valid[0] != prev_valid[0] else 1
                    t = (i - (i - gap)) / gap if gap != 0 else 0
                    
                    interp_x = prev_valid[0] + t * (next_valid[0] - prev_valid[0])
                    interp_y = prev_valid[1] + t * (next_valid[1] - prev_valid[1])
                    result.append((interp_x, interp_y))
                elif prev_valid:
                    result.append(prev_valid)
                elif next_valid:
                    result.append(next_valid)
                else:
                    result.append((0, 0))
        
        return result

class OutlierRemovalStrategy(OptimizationStrategy):
    """异常值移除策略"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="outlier_removal",
            name="异常值移除",
            description="移除轨迹中的异常跳跃点",
            category="cleaning",
            parameters={
                "threshold": 0.1,
                "min_points": 3
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        threshold = kwargs.get('threshold', self.info.parameters['threshold'])
        min_points = kwargs.get('min_points', self.info.parameters['min_points'])
        
        result = []
        valid_points = [(i, point) for i, point in enumerate(trajectory) 
                       if point[0] is not None and point[1] is not None 
                       and not np.isnan(point[0]) and not np.isnan(point[1])]
        
        if len(valid_points) < min_points:
            return trajectory
        
        for i, point in enumerate(trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                result.append((0, 0))
                continue
            
            # 计算与前后点的距离
            is_outlier = False
            if i > 0 and i < len(trajectory) - 1:
                prev_point = trajectory[i-1]
                next_point = trajectory[i+1]
                
                if (prev_point[0] is not None and prev_point[1] is not None and 
                    next_point[0] is not None and next_point[1] is not None):
                    
                    dist_prev = np.sqrt((point[0] - prev_point[0])**2 + (point[1] - prev_point[1])**2)
                    dist_next = np.sqrt((point[0] - next_point[0])**2 + (point[1] - next_point[1])**2)
                    
                    if dist_prev > threshold or dist_next > threshold:
                        is_outlier = True
            
            if is_outlier:
                # 使用前后点的平均值
                if i > 0 and i < len(trajectory) - 1:
                    prev_point = trajectory[i-1]
                    next_point = trajectory[i+1]
                    if (prev_point[0] is not None and prev_point[1] is not None and 
                        next_point[0] is not None and next_point[1] is not None):
                        avg_x = (prev_point[0] + next_point[0]) / 2
                        avg_y = (prev_point[1] + next_point[1]) / 2
                        result.append((avg_x, avg_y))
                    else:
                        result.append(point)
                else:
                    result.append(point)
            else:
                result.append(point)
        
        return result

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, OptimizationStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认策略 - 已禁用，只使用真实策略"""
        pass
    
    def register_strategy(self, strategy: OptimizationStrategy):
        """注册策略"""
        self.strategies[strategy.info.id] = strategy
        print(f"已注册策略: {strategy.info.name} ({strategy.info.id})")
    
    def get_strategy(self, strategy_id: str) -> OptimizationStrategy:
        """获取策略"""
        return self.strategies.get(strategy_id)
    
    def get_all_strategies(self) -> Dict[str, StrategyInfo]:
        """获取所有策略信息"""
        return {strategy_id: strategy.get_info() for strategy_id, strategy in self.strategies.items()}
    
    def get_strategies_by_category(self, category: str) -> Dict[str, StrategyInfo]:
        """按类别获取策略"""
        return {strategy_id: strategy.get_info() 
                for strategy_id, strategy in self.strategies.items() 
                if strategy.info.category == category}
    
    def apply_strategy(self, strategy_id: str, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        """应用策略"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"策略 {strategy_id} 不存在")
        
        return strategy.optimize(trajectory, **kwargs)
    
    def apply_multiple_strategies(self, strategy_ids: List[str], trajectory: List[Tuple[float, float]], **kwargs) -> Dict[str, List[Tuple[float, float]]]:
        """应用多个策略"""
        results = {}
        for strategy_id in strategy_ids:
            try:
                results[strategy_id] = self.apply_strategy(strategy_id, trajectory, **kwargs)
            except Exception as e:
                print(f"应用策略 {strategy_id} 时出错: {e}")
                results[strategy_id] = trajectory
        
        return results

# 全局策略管理器实例
strategy_manager = StrategyManager()

def get_strategy_manager() -> StrategyManager:
    """获取全局策略管理器"""
    return strategy_manager
