#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downswing状态处理器
负责处理下杆阶段的逻辑
"""

from analyzer.swing_states.base_state import BaseStateProcessor, SwingPhase
from typing import Dict, Any

class DownswingStateProcessor(BaseStateProcessor):
    """Downswing状态处理器"""
    
    def process_frame(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Downswing状态的帧数据"""
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        dy = frame_data['dy']
        all_data = frame_data['all_data']
        
        v_fast = self.config['v_fast']
        confidence = self.calculate_confidence(frame_data)
        
        should_transition = False
        next_state = SwingPhase.DOWNSWING
        
        # 检查是否进入Impact（瞬时）
        if self.is_impact_candidate(frame_data):
            should_transition = True
            next_state = SwingPhase.IMPACT
        
        return {
            'new_state': SwingPhase.DOWNSWING,
            'should_transition': should_transition,
            'next_state': next_state,
            'confidence': confidence,
            'debug_info': self.get_debug_info(frame_data)
        }
    
    def is_impact_candidate(self, frame_data: Dict[str, Any]) -> bool:
        """Impact候选判定：
        - 需经过 Transition 结束后的安全间隔（默认5帧）
        - d 局部最小（y 接近最小，dy 前负后正）
        - v 达到高分位（近邻Q80）
        近邻窗口 k=2，Q80 以 [i-3, i+3] 窗口估算。
        """
        frame_idx = frame_data['frame_idx']
        v = frame_data['v']
        dy = frame_data['dy']
        all_data = frame_data['all_data']

        dy_list = all_data['dy_list']
        v_list = all_data['v_list']
        traj = all_data['trajectory']

        # 安全间隔：需在 Transition 结束之后
        safety = frame_data['all_data'].get('impact_safety_after_transition', 2)
        trans_end = all_data.get('transition_end', -1)
        if frame_idx <= trans_end + safety:
            return False

        # 近邻窗口
        k = frame_data['all_data'].get('impact_local_window_k', 2)
        L = len(v_list)
        if frame_idx < k or frame_idx >= L - k:
            return False

        # 条件1：局部最小（用 y 值接近局部最小 + dy 前负后正）
        # y 越小越靠上，这里impact在最低点左右，即 y 局部最大；
        # 由于上游将 y 作为第二维，最低点对应 y 最大，因此用局部最大。
        # 使用轨迹 y 分量趋势判断：dy 前>0 后<0 则为最低点通过后的上升，但我们更接近最低点时刻使用 dy 前>0 且 dy 后<0 切换点附近。
        dy_before = dy_list[frame_idx-1]
        dy_after = dy_list[frame_idx+1]
        direction_switch = (dy_before > 0 and dy_after < 0)

        # y 局部极大（最低点）
        y_vals = [traj[i][1] if traj[i] is not None else 0.0 for i in range(frame_idx-k, frame_idx+k+1)]
        y_center = traj[frame_idx][1] if traj[frame_idx] is not None else 0.0
        is_local_max_y = all(y_center >= y for y in y_vals)

        # 条件2：速度达到高分位（Q80）
        v_win = v_list[max(0, frame_idx-3):min(L, frame_idx+4)]
        if not v_win:
            return False
        v_sorted = sorted(v_win)
        q = frame_data['all_data'].get('impact_v_quantile', 0.7)
        q_idx = int(q * (len(v_sorted)-1))
        qv = v_sorted[q_idx]
        v_high = v >= qv

        # 合并候选条件
        return bool(direction_switch and is_local_max_y and v_high)
    
    def calculate_confidence(self, frame_data: Dict[str, Any]) -> float:
        dy = frame_data['dy']
        return 0.9 if dy > 0 else 0.3
