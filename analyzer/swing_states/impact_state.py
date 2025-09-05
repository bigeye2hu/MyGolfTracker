#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impact状态处理器
负责处理击球阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class ImpactStateProcessor(BaseStateProcessor):
    """Impact状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Impact状态的帧数据"""
        confidence = self.calculate_confidence(frame_data)
        
        # Impact是瞬时事件，立即转换到FollowThrough
        return {
            'new_state': SwingPhase.IMPACT,
            'should_transition': True,
            'next_state': SwingPhase.FOLLOWTHROUGH,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        return 0.9
