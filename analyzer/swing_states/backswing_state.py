#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backswing状态处理器
负责处理上杆阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class BackswingStateProcessor(BaseStateProcessor):
    """Backswing状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理Backswing状态的帧数据
        
        Backswing状态特点：
        - dy < 0 (向上运动)
        - 速度逐渐增加
        - 监控Top候选点
        """
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        dy = frame_data['dy']
        all_data = frame_data['all_data']
        
        # 获取配置参数
        debounce_frames = self.config['debounce_frames']
        local_extrema_window = self.config['local_extrema_window']
        
        # 计算置信度
        confidence = self.calculate_confidence(frame_data)
        
        # 检查是否应该转换到Transition状态
        should_transition = False
        next_state = SwingPhase.BACKSWING
        
        # 监控Top候选点
        if self.is_top_candidate(frame_data):
            # 检查其后dy>0是否可持续
            dy_list = all_data['dy_list']
            if self.check_consecutive_condition(dy_list, frame_idx + 1, '>', 0, debounce_frames):
                should_transition = True
                next_state = SwingPhase.TRANSITION
        
        return {
            'new_state': SwingPhase.BACKSWING,
            'should_transition': should_transition,
            'next_state': next_state,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data),
            'top_candidate': self.is_top_candidate(frame_data)
        }
    
    def is_top_candidate(self, frame_data: Dict[str, Any]) -> bool:
        """检查是否为Top候选点"""
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        dy = frame_data['dy']
        all_data = frame_data['all_data']
        
        v_list = all_data['v_list']
        dy_list = all_data['dy_list']
        k = self.config['local_extrema_window']
        m = self.config['noise_tolerance']
        
        # 简化条件1：v局部极小（放宽要求）
        if frame_idx < k or frame_idx >= len(v_list) - k:
            return False
        
        v_window = v_list[frame_idx-k:frame_idx+k+1]
        # 放宽要求：只要v接近局部最小值即可
        if v > min(v_window) * 1.2:  # 允许20%的误差
            return False
        
        # 简化条件2：dy方向变化检测（放宽要求）
        if frame_idx < m or frame_idx >= len(dy_list) - m:
            return False
        
        # 检查前后几帧的dy趋势
        dy_before = [dy_list[j] for j in range(max(0, frame_idx-m), frame_idx) if j < len(dy_list)]
        dy_after = [dy_list[j] for j in range(frame_idx, min(frame_idx+m+1, len(dy_list)))]
        
        # 放宽要求：只要大部分帧符合趋势即可
        if (len(dy_before) >= 1 and len(dy_after) >= 1 and
            sum(1 for d in dy_before if d < 0) >= len(dy_before) * 0.6 and  # 前几帧大部分dy<0
            sum(1 for d in dy_after if d > 0) >= len(dy_after) * 0.6):      # 后几帧大部分dy>0
            return True
        
        return False
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        """计算Backswing状态的置信度"""
        dy = frame_data['dy']
        
        # dy < 0 的置信度
        if dy < 0:
            confidence = 0.9
        else:
            confidence = 0.3
        
        return confidence
