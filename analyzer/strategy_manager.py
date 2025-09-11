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

class AutoFillStrategy(OptimizationStrategy):
    """自动补齐策略 - 将未检测到的帧自动补齐到最近有效帧位置"""
    
    def __init__(self):
        super().__init__(StrategyInfo(
            id="auto_fill",
            name="自动补齐算法",
            description="将未检测到的帧自动补齐到最近有效帧位置，提高轨迹连续性",
            category="interpolation",
            parameters={
                "max_gap": 10,  # 最大填补间隔
                "interpolation_method": "linear"  # 插值方法
            }
        ))
    
    def optimize(self, trajectory: List[Tuple[float, float]], **kwargs) -> List[Tuple[float, float]]:
        """
        自动补齐轨迹数据
        
        Args:
            trajectory: 原始轨迹数据 [(x, y), ...]
            **kwargs: 额外参数
            
        Returns:
            补齐后的轨迹数据
        """
        if not trajectory or len(trajectory) < 2:
            return trajectory
        
        print(f"🔍 AutoFillStrategy.optimize 输入轨迹长度: {len(trajectory)}")
        print(f"🔍 前10个点: {trajectory[:10]}")
        print(f"🔍 第17个点: {trajectory[17] if len(trajectory) > 17 else '不存在'}")
        
        # 转换为numpy数组便于处理
        traj_array = np.array(trajectory)
        x_coords = traj_array[:, 0]
        y_coords = traj_array[:, 1]
        
        # 识别有效检测点（非零且非None坐标）
        # 首先处理None值：将None转换为0
        x_coords_clean = np.array([0 if x is None else x for x in x_coords])
        y_coords_clean = np.array([0 if y is None else y for y in y_coords])
        
        # 检查是否为有效点（非零坐标）
        valid_mask = (x_coords_clean != 0) & (y_coords_clean != 0)
        valid_indices = np.where(valid_mask)[0]
        
        print(f"🔍 有效检测点索引: {valid_indices[:10]}... (共{len(valid_indices)}个)")
        print(f"🔍 第17帧坐标: x={x_coords[17]}, y={y_coords[17]}")
        print(f"🔍 第17帧是否有效: {valid_mask[17]}")
        
        if len(valid_indices) < 2:
            print("❌ 有效检测点少于2个，无法补齐")
            return trajectory
        
        # 补齐缺失的帧
        filled_x = self._fill_missing_frames(x_coords_clean, valid_indices)
        filled_y = self._fill_missing_frames(y_coords_clean, valid_indices)
        
        # 重新组合轨迹
        filled_trajectory = list(zip(filled_x, filled_y))
        
        print(f"🔍 补齐后轨迹长度: {len(filled_trajectory)}")
        print(f"🔍 补齐后第17个点: {filled_trajectory[17] if len(filled_trajectory) > 17 else '不存在'}")
        
        return filled_trajectory
    
    def _fill_missing_frames(self, coords: np.ndarray, valid_indices: np.ndarray) -> np.ndarray:
        """
        填补缺失帧的坐标
        
        Args:
            coords: 坐标数组
            valid_indices: 有效检测点的索引
            
        Returns:
            填补后的坐标数组
        """
        filled_coords = coords.copy()
        max_gap = self.info.parameters.get("max_gap", 10)
        
        print(f"🔍 _fill_missing_frames 开始，max_gap={max_gap}")
        print(f"🔍 有效索引: {valid_indices[:10]}... (共{len(valid_indices)}个)")
        
        for i in range(len(valid_indices) - 1):
            start_idx = valid_indices[i]
            end_idx = valid_indices[i + 1]
            gap_size = end_idx - start_idx - 1
            
            if gap_size > 0:
                print(f"🔍 检查间隔 {start_idx} -> {end_idx}, 间隔大小: {gap_size}")
            
            # 只填补小间隔的缺失帧
            if 0 < gap_size <= max_gap:
                start_val = coords[start_idx]
                end_val = coords[end_idx]
                
                print(f"🔍 填补间隔 {start_idx}-{end_idx}: {start_val} -> {end_val}")
                
                # 线性插值填补
                for j in range(1, gap_size + 1):
                    alpha = j / (gap_size + 1)
                    interpolated_val = start_val + alpha * (end_val - start_val)
                    filled_coords[start_idx + j] = interpolated_val
                    print(f"🔍   填补位置 {start_idx + j}: {interpolated_val}")
            elif gap_size > max_gap:
                print(f"🔍 间隔 {start_idx}-{end_idx} 太大 ({gap_size} > {max_gap})，跳过")
        
        print(f"🔍 填补完成，第17帧值: {filled_coords[17]}")
        return filled_coords


# 只保留AutoFillStrategy，其他策略已删除

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, OptimizationStrategy] = {}
        self.register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认策略 - 已禁用，只使用真实策略"""
        pass
    
    def register_strategy(self, strategy: OptimizationStrategy):
        """注册策略"""
        self.strategies[strategy.info.id] = strategy
        print(f"已注册策略: {strategy.info.name} ({strategy.info.id})")
    
    def register_default_strategies(self):
        """注册默认策略 - 只注册自动补齐策略"""
        # 只注册自动补齐策略
        auto_fill_strategy = AutoFillStrategy()
        self.register_strategy(auto_fill_strategy)
    
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
