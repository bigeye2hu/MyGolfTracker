#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finish状态处理器
负责处理完成阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class FinishStateProcessor(BaseStateProcessor):
    """Finish状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Finish状态的帧数据"""
        confidence = self.calculate_confidence(frame_data)
        
        # Finish是最终状态，不转换
        return {
            'new_state': SwingPhase.FINISH,
            'should_transition': False,
            'next_state': SwingPhase.FINISH,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        v = frame_data['v']
        v_finish = self.config['v_finish']
        
        # 速度越低，置信度越高
        return max(0, 1.0 - (v / v_finish))
