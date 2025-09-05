#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态处理器基类
所有具体状态处理器都继承自此类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class SwingPhase(Enum):
    """挥杆阶段枚举"""
    ADDRESS = "Address"           # 准备
    BACKSWING = "Backswing"       # 上杆
    TRANSITION = "Transition"     # 过渡
    DOWNSWING = "Downswing"       # 下杆
    IMPACT = "Impact"             # 击球
    FOLLOWTHROUGH = "FollowThrough"  # 随挥
    FINISH = "Finish"             # 完成
    UNKNOWN = "Unknown"           # 未知

class BaseStateProcessor(ABC):
    """状态处理器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化状态处理器
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.state_name = self.__class__.__name__.replace('StateProcessor', '')
    
    @abstractmethod
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单帧数据
        
        Args:
            frame_data: 帧数据字典，包含：
                - frame_idx: 帧索引
                - trajectory: 杆头位置
                - dx, dy, v: 位移和速度
                - current_state: 当前状态
                - state_start_frame: 状态开始帧
                - all_data: 所有数据
                
        Returns:
            处理结果字典，包含：
                - new_state: 当前帧的新状态
                - should_transition: 是否需要状态转换
                - next_state: 下一个状态（如果需要转换）
                - confidence: 置信度
                - debug_info: 调试信息
        """
        pass
    
    def check_consecutive_condition(self, data_list: list, start_idx: int, 
                                  operator: str, threshold: float, count: int) -> bool:
        """
        检查连续条件（去抖机制）
        
        Args:
            data_list: 数据列表
            start_idx: 开始索引
            operator: 操作符 ('<', '>', '<=', '>=', '==')
            threshold: 阈值
            count: 连续帧数要求
            
        Returns:
            是否满足连续条件
        """
        if start_idx >= len(data_list) - count + 1:
            return False
        
        consecutive_count = 0
        for i in range(start_idx, min(start_idx + count, len(data_list))):
            value = data_list[i]
            
            if operator == '<' and value < threshold:
                consecutive_count += 1
            elif operator == '>' and value > threshold:
                consecutive_count += 1
            elif operator == '<=' and value <= threshold:
                consecutive_count += 1
            elif operator == '>=' and value >= threshold:
                consecutive_count += 1
            elif operator == '==' and value == threshold:
                consecutive_count += 1
            else:
                consecutive_count = 0  # 重置计数器
        
        return consecutive_count >= count
    
    def find_local_extrema(self, data: list, window_size: int = 3, 
                          extrema_type: str = 'min') -> list:
        """
        找到局部极值点
        
        Args:
            data: 数据列表
            window_size: 窗口大小
            extrema_type: 极值类型 ('min' 或 'max')
            
        Returns:
            极值点索引列表
        """
        if len(data) < window_size:
            return []
        
        extrema = []
        half_window = window_size // 2
        
        for i in range(half_window, len(data) - half_window):
            is_extremum = True
            current_value = data[i]
            
            for j in range(i - half_window, i + half_window + 1):
                if j != i:
                    if extrema_type == 'min' and data[j] < current_value:
                        is_extremum = False
                        break
                    elif extrema_type == 'max' and data[j] > current_value:
                        is_extremum = False
                        break
            
            if is_extremum:
                extrema.append(i)
        
        return extrema
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        """
        计算当前状态的置信度
        
        Args:
            frame_data: 帧数据
            
        Returns:
            置信度 (0.0 - 1.0)
        """
        # 默认实现，子类可以重写
        return 0.8
    
    def get_debug_info(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取调试信息
        
        Args:
            frame_data: 帧数据
            
        Returns:
            调试信息字典
        """
        return {
            'state_name': self.state_name,
            'frame_idx': frame_data.get('frame_idx', -1),
            'current_state': frame_data.get('current_state', SwingPhase.UNKNOWN).value,
            'dx': frame_data.get('dx', 0.0),
            'dy': frame_data.get('dy', 0.0),
            'v': frame_data.get('v', 0.0)
        }
