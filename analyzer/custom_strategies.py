#!/usr/bin/env python3
"""
自定义策略配置 - 用户可以在这里定义自己的策略
"""

from analyzer.strategy_manager import OptimizationStrategy, StrategyInfo
from typing import List, Tuple
import numpy as np

class CustomSmoothingStrategy(OptimizationStrategy):
    """自定义平滑策略 - 针对高尔夫挥杆优化"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="custom_smoothing",
            name="高尔夫挥杆平滑",
            description="专门为高尔夫挥杆轨迹设计的平滑算法，保持挥杆的流畅性",
            category="golf_specific",
            parameters={
                "smooth_factor": 0.3,
                "velocity_threshold": 0.05
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        smooth_factor = kwargs.get('smooth_factor', self.info.parameters['smooth_factor'])
        velocity_threshold = kwargs.get('velocity_threshold', self.info.parameters['velocity_threshold'])
        
        result = []
        for i, point in enumerate(trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                result.append((0, 0))
                continue
            
            if i == 0 or i == len(trajectory) - 1:
                result.append(point)
                continue
            
            # 计算速度
            prev_point = trajectory[i-1]
            next_point = trajectory[i+1]
            
            if (prev_point[0] is not None and prev_point[1] is not None and 
                next_point[0] is not None and next_point[1] is not None):
                
                vx = (next_point[0] - prev_point[0]) / 2
                vy = (next_point[1] - prev_point[1]) / 2
                velocity = np.sqrt(vx**2 + vy**2)
                
                # 根据速度调整平滑程度
                if velocity > velocity_threshold:
                    # 高速移动时减少平滑
                    current_smooth = smooth_factor * 0.5
                else:
                    # 低速移动时增加平滑
                    current_smooth = smooth_factor * 1.5
                
                # 应用平滑
                smoothed_x = point[0] + current_smooth * (prev_point[0] + next_point[0] - 2 * point[0])
                smoothed_y = point[1] + current_smooth * (prev_point[1] + next_point[1] - 2 * point[1])
                
                result.append((smoothed_x, smoothed_y))
            else:
                result.append(point)
        
        return result

class FastMotionStrategy(OptimizationStrategy):
    """快速移动优化策略 - 针对快速挥杆"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="fast_motion",
            name="快速移动优化",
            description="专门处理快速移动物体的轨迹优化，减少延迟和跳跃",
            category="motion",
            parameters={
                "prediction_frames": 2,
                "smoothing_window": 3
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        prediction_frames = kwargs.get('prediction_frames', self.info.parameters['prediction_frames'])
        smoothing_window = kwargs.get('smoothing_window', self.info.parameters['smoothing_window'])
        
        result = []
        for i, point in enumerate(trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                result.append((0, 0))
                continue
            
            if i < prediction_frames:
                result.append(point)
                continue
            
            # 使用历史数据预测
            history_points = []
            for j in range(max(0, i - smoothing_window), i):
                if (trajectory[j][0] is not None and trajectory[j][1] is not None and 
                    not np.isnan(trajectory[j][0]) and not np.isnan(trajectory[j][1])):
                    history_points.append(trajectory[j])
            
            if len(history_points) >= 2:
                # 计算平均速度
                vx_sum = 0
                vy_sum = 0
                for j in range(1, len(history_points)):
                    vx_sum += history_points[j][0] - history_points[j-1][0]
                    vy_sum += history_points[j][1] - history_points[j-1][1]
                
                avg_vx = vx_sum / (len(history_points) - 1)
                avg_vy = vy_sum / (len(history_points) - 1)
                
                # 预测当前位置
                predicted_x = history_points[-1][0] + avg_vx
                predicted_y = history_points[-1][1] + avg_vy
                
                # 混合预测和实际检测
                alpha = 0.7  # 预测权重
                final_x = alpha * predicted_x + (1 - alpha) * point[0]
                final_y = alpha * predicted_y + (1 - alpha) * point[1]
                
                result.append((final_x, final_y))
            else:
                result.append(point)
        
        return result

class ConservativeStrategy(OptimizationStrategy):
    """保守策略 - 最小化修改原始数据"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="conservative",
            name="保守优化",
            description="最小化修改原始检测数据，只在必要时进行轻微调整",
            category="conservative",
            parameters={
                "max_adjustment": 0.02,
                "confidence_threshold": 0.8
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        max_adjustment = kwargs.get('max_adjustment', self.info.parameters['max_adjustment'])
        confidence_threshold = kwargs.get('confidence_threshold', self.info.parameters['confidence_threshold'])
        
        result = []
        for i, point in enumerate(trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                result.append((0, 0))
                continue
            
            if i == 0 or i == len(trajectory) - 1:
                result.append(point)
                continue
            
            # 检查是否需要调整
            prev_point = trajectory[i-1]
            next_point = trajectory[i+1]
            
            if (prev_point[0] is not None and prev_point[1] is not None and 
                next_point[0] is not None and next_point[1] is not None):
                
                # 计算与相邻点的距离
                dist_prev = np.sqrt((point[0] - prev_point[0])**2 + (point[1] - prev_point[1])**2)
                dist_next = np.sqrt((point[0] - next_point[0])**2 + (point[1] - next_point[1])**2)
                
                # 只有在距离异常大时才进行调整
                if dist_prev > max_adjustment or dist_next > max_adjustment:
                    # 轻微调整到中间位置
                    adjusted_x = point[0] + 0.1 * (prev_point[0] + next_point[0] - 2 * point[0])
                    adjusted_y = point[1] + 0.1 * (prev_point[1] + next_point[1] - 2 * point[1])
                    result.append((adjusted_x, adjusted_y))
                else:
                    result.append(point)
            else:
                result.append(point)
        
        return result

class FirstOptimizationStrategy(OptimizationStrategy):
    """第一优化策略 - 杆头专用优化算法"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="first_optimization",
            name="第一优化策略",
            description="专门为高尔夫杆头轨迹设计的优化算法，结合平滑和预测技术",
            category="golf_specific",
            parameters={
                "smooth_factor": 0.4,
                "prediction_weight": 0.3,
                "velocity_threshold": 0.08,
                "window_size": 5
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        if len(trajectory) < 3:
            return trajectory
        
        smooth_factor = kwargs.get('smooth_factor', self.info.parameters['smooth_factor'])
        prediction_weight = kwargs.get('prediction_weight', self.info.parameters['prediction_weight'])
        velocity_threshold = kwargs.get('velocity_threshold', self.info.parameters['velocity_threshold'])
        window_size = kwargs.get('window_size', self.info.parameters['window_size'])
        
        result = []
        for i, point in enumerate(trajectory):
            if point[0] is None or point[1] is None or np.isnan(point[0]) or np.isnan(point[1]):
                result.append((0, 0))
                continue
            
            if i == 0 or i == len(trajectory) - 1:
                result.append(point)
                continue
            
            # 计算运动速度
            prev_point = trajectory[i-1]
            next_point = trajectory[i+1] if i < len(trajectory) - 1 else point
            
            if (prev_point[0] is not None and prev_point[1] is not None and 
                next_point[0] is not None and next_point[1] is not None):
                
                # 计算速度
                vx = (next_point[0] - prev_point[0]) / 2
                vy = (next_point[1] - prev_point[1]) / 2
                velocity = np.sqrt(vx**2 + vy**2)
                
                # 根据速度调整优化策略
                if velocity > velocity_threshold:
                    # 高速移动：使用预测算法
                    predicted_x = prev_point[0] + vx * 2
                    predicted_y = prev_point[1] + vy * 2
                    
                    # 混合预测和实际检测
                    final_x = point[0] + prediction_weight * (predicted_x - point[0])
                    final_y = point[1] + prediction_weight * (predicted_y - point[1])
                else:
                    # 低速移动：使用平滑算法
                    # 计算窗口内的平均值
                    start_idx = max(0, i - window_size // 2)
                    end_idx = min(len(trajectory), i + window_size // 2 + 1)
                    
                    window_points = []
                    for j in range(start_idx, end_idx):
                        if (trajectory[j][0] is not None and trajectory[j][1] is not None and 
                            not np.isnan(trajectory[j][0]) and not np.isnan(trajectory[j][1])):
                            window_points.append(trajectory[j])
                    
                    if len(window_points) >= 2:
                        avg_x = sum(p[0] for p in window_points) / len(window_points)
                        avg_y = sum(p[1] for p in window_points) / len(window_points)
                        
                        # 应用平滑
                        final_x = point[0] + smooth_factor * (avg_x - point[0])
                        final_y = point[1] + smooth_factor * (avg_y - point[1])
                    else:
                        final_x, final_y = point
                
                result.append((final_x, final_y))
            else:
                result.append(point)
        
        return result

# 注册自定义策略的函数
def register_custom_strategies(strategy_manager):
    """注册所有自定义策略"""
    custom_strategies = [
        CustomSmoothingStrategy(),
        FastMotionStrategy(),
        ConservativeStrategy(),
        FirstOptimizationStrategy()
    ]
    
    for strategy in custom_strategies:
        strategy_manager.register_strategy(strategy)
    
    print(f"已注册 {len(custom_strategies)} 个自定义策略")