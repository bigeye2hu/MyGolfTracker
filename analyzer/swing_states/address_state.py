#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Address状态处理器
负责处理准备阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class AddressStateProcessor(BaseStateProcessor):
    """Address状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理Address状态的帧数据
        
        Address状态特点：
        - 速度较低 (v < v_address)
        - 位置相对稳定
        - 杆头在球后准备位置
        """
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        dy = frame_data['dy']
        trajectory = frame_data['trajectory']
        all_data = frame_data['all_data']
        
        # 获取配置参数
        v_address = self.config['v_address']
        debounce_frames = self.config['debounce_frames']
        
        # 计算置信度
        confidence = self.calculate_confidence(frame_data)
        
        # 检查是否应该转换到Backswing状态
        should_transition = False
        next_state = SwingPhase.ADDRESS
        
        # 条件1: 速度超过Address阈值
        if v > v_address:
            # 检查连续条件（去抖）
            dy_list = all_data['dy_list']
            if self.check_consecutive_condition(dy_list, frame_idx, '<', 0, debounce_frames):
                # dy < 0 连续多帧，表示开始上杆
                should_transition = True
                next_state = SwingPhase.BACKSWING
        
        # 条件2: 位置检查（可选）
        if trajectory is not None and len(trajectory) >= 2:
            x, y = trajectory[0], trajectory[1]
            # 检查是否在合理的Address位置范围
            if not (0.3 <= x <= 0.8 and 0.3 <= y <= 0.8):
                # 位置异常，可能需要转换
                pass
        
        return {
            'new_state': SwingPhase.ADDRESS,
            'should_transition': should_transition,
            'next_state': next_state,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        """计算Address状态的置信度"""
        v = frame_data['v']
        v_address = self.config['v_address']
        trajectory = frame_data['trajectory']
        
        # 基础置信度：速度越低，置信度越高
        speed_confidence = max(0, 1.0 - (v / v_address))
        
        # 位置置信度
        position_confidence = 1.0
        if trajectory is not None and len(trajectory) >= 2:
            x, y = trajectory[0], trajectory[1]
            # 检查是否在合理的Address位置
            if 0.3 <= x <= 0.8 and 0.3 <= y <= 0.8:
                position_confidence = 1.0
            else:
                position_confidence = 0.5
        
        # 综合置信度
        confidence = (speed_confidence + position_confidence) / 2
        return min(1.0, max(0.0, confidence))
