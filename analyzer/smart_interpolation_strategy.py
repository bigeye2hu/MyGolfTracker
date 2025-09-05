#!/usr/bin/env python3
"""
智能插值策略 - 专门用于补齐缺失帧，不调整已检测的杆头位置
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from analyzer.strategy_manager import OptimizationStrategy, StrategyInfo

class SmartInterpolationStrategy(OptimizationStrategy):
    """智能插值策略 - 只补齐缺失帧，保持已检测位置不变"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="smart_interpolation",
            name="智能插值策略",
            description="专门用于补齐缺失帧，保持已检测的杆头位置完全不变，确保轨迹不乱窜",
            category="conservative",
            parameters={
                "max_gap_size": 10,  # 最大连续缺失帧数
                "min_valid_points": 2,  # 插值所需的最少有效点数
                "smooth_transition": True  # 是否平滑过渡
            }
        ))
    
    def optimize(self, trajectory: List[List[float]], **kwargs) -> List[List[float]]:
        """
        优化轨迹 - 只补齐缺失帧，不调整已检测位置
        
        Args:
            trajectory: 原始轨迹，格式为[[x1,y1], [x2,y2], ...]
                       缺失帧用[0,0]表示
            
        Returns:
            优化后的轨迹，已检测位置保持不变
        """
        if len(trajectory) < 2:
            return trajectory
        
        print(f"🔍 智能插值策略开始处理，轨迹长度: {len(trajectory)}")
        
        # 1. 识别缺失帧和有效帧
        missing_indices = []
        valid_points = []
        
        for i, point in enumerate(trajectory):
            if self._is_missing_point(point):
                missing_indices.append(i)
            else:
                valid_points.append((i, point))
        
        print(f"📊 发现 {len(missing_indices)} 个缺失帧: {missing_indices}")
        print(f"📊 发现 {len(valid_points)} 个有效点")
        
        # 如果没有缺失帧，直接返回原轨迹
        if not missing_indices:
            print("✅ 没有缺失帧，直接返回原轨迹")
            return trajectory
        
        # 2. 补齐缺失帧
        result = trajectory.copy()
        
        for missing_idx in missing_indices:
            interpolated_point = self._interpolate_missing_point(
                trajectory, missing_idx, valid_points
            )
            if interpolated_point is not None:
                result[missing_idx] = interpolated_point
                print(f"🔧 补齐帧 {missing_idx}: {interpolated_point}")
            else:
                print(f"⚠️ 无法补齐帧 {missing_idx}，保持原值")
        
        # 3. 验证结果
        self._validate_result(trajectory, result, missing_indices)
        
        return result
    
    def _is_missing_point(self, point: List[float]) -> bool:
        """判断是否为缺失点"""
        if not point or len(point) < 2:
            return True
        
        x, y = point[0], point[1]
        
        # 检查是否为[0,0]或无效值
        if x == 0.0 and y == 0.0:
            return True
        
        # 检查是否为NaN或无穷大
        try:
            if np.isnan(float(x)) or np.isnan(float(y)) or np.isinf(float(x)) or np.isinf(float(y)):
                return True
        except (ValueError, TypeError):
            return True
        
        return False
    
    def _interpolate_missing_point(self, trajectory: List[List[float]], 
                                 missing_idx: int, 
                                 valid_points: List[Tuple[int, List[float]]]) -> List[float]:
        """
        插值单个缺失点
        
        Args:
            trajectory: 原始轨迹
            missing_idx: 缺失帧索引
            valid_points: 所有有效点列表 [(index, point), ...]
            
        Returns:
            插值后的点，如果无法插值则返回None
        """
        # 找到前后最近的有效点
        prev_point = None
        next_point = None
        prev_idx = -1
        next_idx = len(trajectory)
        
        for valid_idx, valid_point in valid_points:
            if valid_idx < missing_idx and valid_idx > prev_idx:
                prev_point = valid_point
                prev_idx = valid_idx
            elif valid_idx > missing_idx and valid_idx < next_idx:
                next_point = valid_point
                next_idx = valid_idx
        
        # 情况1: 前后都有有效点 - 线性插值
        if prev_point is not None and next_point is not None:
            return self._linear_interpolate(
                prev_point, prev_idx, next_point, next_idx, missing_idx
            )
        
        # 情况2: 只有前一个有效点 - 外推
        elif prev_point is not None:
            return self._extrapolate_forward(
                prev_point, prev_idx, missing_idx, trajectory
            )
        
        # 情况3: 只有后一个有效点 - 外推
        elif next_point is not None:
            return self._extrapolate_backward(
                next_point, next_idx, missing_idx, trajectory
            )
        
        # 情况4: 没有有效点 - 无法插值
        else:
            return None
    
    def _linear_interpolate(self, prev_point: List[float], prev_idx: int,
                          next_point: List[float], next_idx: int,
                          target_idx: int) -> List[float]:
        """线性插值"""
        # 计算插值比例
        ratio = (target_idx - prev_idx) / (next_idx - prev_idx)
        
        # 线性插值
        x = prev_point[0] + ratio * (next_point[0] - prev_point[0])
        y = prev_point[1] + ratio * (next_point[1] - prev_point[1])
        
        return [x, y]
    
    def _extrapolate_forward(self, prev_point: List[float], prev_idx: int,
                           target_idx: int, trajectory: List[List[float]]) -> List[float]:
        """向前外推"""
        # 寻找更早的有效点来计算速度
        earlier_point = None
        earlier_idx = -1
        
        for i in range(prev_idx - 1, -1, -1):
            if not self._is_missing_point(trajectory[i]):
                earlier_point = trajectory[i]
                earlier_idx = i
                break
        
        if earlier_point is not None:
            # 计算速度
            dx = prev_point[0] - earlier_point[0]
            dy = prev_point[1] - earlier_point[1]
            dt = prev_idx - earlier_idx
            
            if dt > 0:
                vx = dx / dt
                vy = dy / dt
                
                # 外推
                steps = target_idx - prev_idx
                x = prev_point[0] + vx * steps
                y = prev_point[1] + vy * steps
                
                return [x, y]
        
        # 如果无法计算速度，直接使用前一个点
        return prev_point.copy()
    
    def _extrapolate_backward(self, next_point: List[float], next_idx: int,
                            target_idx: int, trajectory: List[List[float]]) -> List[float]:
        """向后外推"""
        # 寻找更晚的有效点来计算速度
        later_point = None
        later_idx = len(trajectory)
        
        for i in range(next_idx + 1, len(trajectory)):
            if not self._is_missing_point(trajectory[i]):
                later_point = trajectory[i]
                later_idx = i
                break
        
        if later_point is not None:
            # 计算速度
            dx = later_point[0] - next_point[0]
            dy = later_point[1] - next_point[1]
            dt = later_idx - next_idx
            
            if dt > 0:
                vx = dx / dt
                vy = dy / dt
                
                # 外推
                steps = target_idx - next_idx
                x = next_point[0] + vx * steps
                y = next_point[1] + vy * steps
                
                return [x, y]
        
        # 如果无法计算速度，直接使用后一个点
        return next_point.copy()
    
    def _validate_result(self, original: List[List[float]], 
                        result: List[List[float]], 
                        missing_indices: List[int]):
        """验证结果"""
        print(f"🔍 验证结果:")
        
        # 检查长度
        if len(original) != len(result):
            print(f"❌ 长度不匹配: {len(original)} vs {len(result)}")
            return
        
        # 检查已检测位置是否被修改
        modified_count = 0
        for i, (orig, res) in enumerate(zip(original, result)):
            if i not in missing_indices and orig != res:
                modified_count += 1
                print(f"❌ 已检测位置被修改: 帧{i} {orig} → {res}")
        
        if modified_count == 0:
            print(f"✅ 所有已检测位置保持不变")
        else:
            print(f"❌ 发现 {modified_count} 个已检测位置被修改")
        
        # 检查缺失帧是否被补齐
        filled_count = 0
        for i in missing_indices:
            if not self._is_missing_point(result[i]):
                filled_count += 1
        
        print(f"📊 补齐了 {filled_count}/{len(missing_indices)} 个缺失帧")

# 注册策略的函数
def register_smart_interpolation_strategy(strategy_manager):
    """注册智能插值策略"""
    strategy = SmartInterpolationStrategy()
    strategy_manager.register_strategy(strategy)
    print(f"已注册策略: {strategy.info.name} ({strategy.info.id})")
    return strategy
