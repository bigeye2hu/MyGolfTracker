#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FollowThrough状态处理器
负责处理随挥阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class FollowThroughStateProcessor(BaseStateProcessor):
    """FollowThrough状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理FollowThrough状态的帧数据"""
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        all_data = frame_data['all_data']
        
        v_finish = self.config['v_finish']
        debounce_frames = self.config['debounce_frames']
        confidence = self.calculate_confidence(frame_data)
        
        should_transition = False
        next_state = SwingPhase.FOLLOWTHROUGH
        
        # 检查是否进入Finish
        if self.check_consecutive_condition(all_data['v_list'], frame_idx, '<', v_finish, debounce_frames):
            should_transition = True
            next_state = SwingPhase.FINISH
        
        return {
            'new_state': SwingPhase.FOLLOWTHROUGH,
            'should_transition': should_transition,
            'next_state': next_state,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        return 0.8
