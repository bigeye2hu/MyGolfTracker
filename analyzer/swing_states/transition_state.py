#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transition状态处理器
负责处理过渡阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class TransitionStateProcessor(BaseStateProcessor):
    """Transition状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Transition状态的帧数据"""
        frame_idx = frame_data['frame_idx']
        dy = frame_data['dy']
        all_data = frame_data['all_data']
        
        debounce_frames = self.config['debounce_frames']
        confidence = self.calculate_confidence(frame_data)
        
        should_transition = False
        next_state = SwingPhase.TRANSITION
        
        # 检查是否进入Downswing
        if self.check_consecutive_condition(all_data['dy_list'], frame_idx, '>', 0, debounce_frames):
            should_transition = True
            next_state = SwingPhase.DOWNSWING
        
        return {
            'new_state': SwingPhase.TRANSITION,
            'should_transition': should_transition,
            'next_state': next_state,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        return 0.8
