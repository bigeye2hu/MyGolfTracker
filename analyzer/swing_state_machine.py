#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挥杆状态机 - 主控制器
采用总分总架构设计

总：主控制器负责整体流程
分：各个状态处理器负责具体状态逻辑
总：后处理器负责结果总结和优化
"""

import json
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path

# 导入各个状态处理器
from analyzer.swing_states.address_state import AddressStateProcessor
from analyzer.swing_states.backswing_state import BackswingStateProcessor
from analyzer.swing_states.transition_state import TransitionStateProcessor
from analyzer.swing_states.downswing_state import DownswingStateProcessor
from analyzer.swing_states.impact_state import ImpactStateProcessor
from analyzer.swing_states.followthrough_state import FollowThroughStateProcessor
from analyzer.swing_states.finish_state import FinishStateProcessor

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

class SwingStateMachine:
    """挥杆状态机主控制器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化状态机
        
        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        
        # 初始化各个状态处理器
        self.state_processors = {
            SwingPhase.ADDRESS: AddressStateProcessor(self.config),
            SwingPhase.BACKSWING: BackswingStateProcessor(self.config),
            SwingPhase.TRANSITION: TransitionStateProcessor(self.config),
            SwingPhase.DOWNSWING: DownswingStateProcessor(self.config),
            SwingPhase.IMPACT: ImpactStateProcessor(self.config),
            SwingPhase.FOLLOWTHROUGH: FollowThroughStateProcessor(self.config),
            SwingPhase.FINISH: FinishStateProcessor(self.config),
        }
        
        # 状态机状态
        self.current_state = SwingPhase.ADDRESS
        self.state_history = []
        self.frame_data = []
        # Top/Transition 窗口控制
        self.top_idx: Optional[int] = None
        self.transition_window: Optional[Tuple[int, int]] = None
        
    def _normalize_phase(self, phase):
        """将来自子处理器的状态枚举标准化为本模块的SwingPhase。
        说明：子处理器使用的枚举定义在 swing_states/base_state.py，与此处的SwingPhase不是同一类。
        这里按 value 做映射，保证控制器内部始终使用统一的SwingPhase。
        """
        try:
            if isinstance(phase, SwingPhase):
                return phase
            # 其他枚举类型或具备 .value 的对象
            value = getattr(phase, 'value', None)
            if value is not None:
                return SwingPhase(value)
        except Exception:
            pass
        # 回退
        return SwingPhase.UNKNOWN

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            # 速度阈值 - 调整更宽松
            'v_address': 0.005,     # Address阶段速度阈值（降低）
            'v_fast': 0.03,         # 快速运动阈值（降低）
            'v_finish': 0.003,      # Finish阶段速度阈值（降低）
            
            # 去抖参数 - 减少去抖要求
            'debounce_frames': 3,   # 连续帧数要求（从5降到3）
            'noise_tolerance': 2,   # 噪声容忍帧数（从3降到2）
            
            # 检测参数
            'local_extrema_window': 3,  # 局部极值窗口
            'impact_safety_margin': 8,  # Impact搜索安全边距（减少）
            
            # 状态转换参数
            'transition_window': 3,     # 过渡窗口大小（减少）
            'impact_threshold': 0.08,   # 击球位置阈值（降低）
            'impact_safety_after_transition': 2,  # Transition 结束后安全间隔帧数（原5，调小便于更早命中）
            'impact_v_quantile': 0.7,   # 速度分位阈值Q（原0.8，调至0.7）
            'impact_local_window_k': 2, # 局部窗口k（±k）

            # Top/Transition 窗口参数
            'top_window_pre': 3,        # Top 窗口前 t1
            'top_window_post': 5,       # Top 窗口后 t2
            'n_down_after_top': 3,      # 窗口后连续 dy>0 的最少帧数
        }
    
    def analyze_swing(self, trajectory: List) -> List[SwingPhase]:
        """
        分析挥杆轨迹，返回各帧的状态
        
        Args:
            trajectory: 杆头轨迹数据
            
        Returns:
            各帧的挥杆状态列表
        """
        print("🎯 开始挥杆状态分析...")
        
        # 总：数据预处理
        processed_data = self._preprocess_data(trajectory)
        
        # 分：状态机执行
        phases = self._execute_state_machine(processed_data)
        
        # 总：后处理优化
        final_phases = self._postprocess_phases(phases, processed_data)
        
        print("✅ 挥杆状态分析完成")
        return final_phases
    
    def _preprocess_data(self, trajectory: List) -> Dict:
        """
        数据预处理 - 计算速度、位移等基础数据
        
        Args:
            trajectory: 原始轨迹数据
            
        Returns:
            处理后的数据字典
        """
        print("📊 数据预处理...")
        
        # 计算速度和位移
        dx_list, dy_list, v_list = self._calculate_velocities(trajectory)
        
        # 计算其他特征
        processed_data = {
            'trajectory': trajectory,
            'dx_list': dx_list,
            'dy_list': dy_list,
            'v_list': v_list,
            'num_frames': len(trajectory),
            'valid_frames': [i for i, p in enumerate(trajectory) if p is not None]
        }
        # 速度分位数（供Downswing早触发使用）
        if v_list:
            vs = sorted(v_list)
            q80 = vs[int(0.8 * (len(vs) - 1))]
            processed_data['v_q80'] = q80
        
        print(f"   处理了 {len(trajectory)} 帧数据")
        print(f"   有效帧数: {len(processed_data['valid_frames'])}")
        
        return processed_data
    
    def _calculate_velocities(self, trajectory: List) -> Tuple[List, List, List]:
        """计算轨迹的速度和位移"""
        dx_list = []
        dy_list = []
        v_list = []
        
        for i in range(1, len(trajectory)):
            if (trajectory[i] is not None and trajectory[i-1] is not None and 
                len(trajectory[i]) >= 2 and len(trajectory[i-1]) >= 2):
                
                dx = trajectory[i][0] - trajectory[i-1][0]
                dy = trajectory[i][1] - trajectory[i-1][1]
                v = (dx**2 + dy**2)**0.5
                
                dx_list.append(dx)
                dy_list.append(dy)
                v_list.append(v)
            else:
                # 使用前一个有效值或默认值
                if dx_list:
                    dx_list.append(dx_list[-1])
                    dy_list.append(dy_list[-1])
                    v_list.append(v_list[-1])
                else:
                    dx_list.append(0.0)
                    dy_list.append(0.0)
                    v_list.append(0.0)
        
        return dx_list, dy_list, v_list
    
    def _execute_state_machine(self, data: Dict) -> List[SwingPhase]:
        """
        执行状态机 - 核心逻辑
        
        Args:
            data: 预处理后的数据
            
        Returns:
            各帧的状态列表
        """
        print("🔄 执行状态机...")
        
        trajectory = data['trajectory']
        dx_list = data['dx_list']
        dy_list = data['dy_list']
        v_list = data['v_list']
        
        # 初始化状态数组
        phases = [SwingPhase.UNKNOWN] * len(trajectory)
        
        # 状态机执行
        current_state = SwingPhase.ADDRESS
        state_start_frame = 0
        
        for frame_idx in range(len(trajectory)):
            # 标准化当前状态，避免跨模块枚举类型不一致
            current_state = self._normalize_phase(current_state)
            frame_data = {
                'frame_idx': frame_idx,
                'trajectory': trajectory[frame_idx] if frame_idx < len(trajectory) else None,
                'dx': dx_list[frame_idx] if frame_idx < len(dx_list) else 0.0,
                'dy': dy_list[frame_idx] if frame_idx < len(dy_list) else 0.0,
                'v': v_list[frame_idx] if frame_idx < len(v_list) else 0.0,
                'current_state': current_state,
                'state_start_frame': state_start_frame,
                'all_data': data
            }
            
            # 获取当前状态的处理器
            processor = self.state_processors.get(current_state)
            if processor is None:
                phases[frame_idx] = SwingPhase.UNKNOWN
                continue
            
            # 执行状态处理
            result = processor.process_frame(frame_data)
            
            # 更新状态
            phases[frame_idx] = self._normalize_phase(result.get('new_state'))

            # ---------- Top/Transition 窗口控制逻辑 ----------
            # 1) 发现 Top 候选：建立窗口并将窗口内标注为 Transition
            if result.get('top_candidate') and self.top_idx is None:
                self.top_idx = frame_idx
                t1 = self.config['top_window_pre']
                t2 = self.config['top_window_post']
                win_l = max(0, self.top_idx - t1)
                win_r = min(len(trajectory) - 1, self.top_idx + t2)
                self.transition_window = (win_l, win_r)
                for k in range(win_l, frame_idx + 1):
                    phases[k] = SwingPhase.TRANSITION
                phases[frame_idx] = SwingPhase.TRANSITION
                current_state = SwingPhase.TRANSITION

            # 2) 若处于 Transition 窗口内，强制为 Transition
            if self.transition_window is not None:
                win_l, win_r = self.transition_window
                if win_l <= frame_idx <= win_r:
                    # 默认标注为Transition
                    phases[frame_idx] = SwingPhase.TRANSITION
                    current_state = SwingPhase.TRANSITION
                    # 早触发Downswing：dy>0连续且速度较高(Q80)
                    N = self.config['n_down_after_top']
                    v_q80 = data.get('v_q80', None)
                    if v_q80 is not None:
                        if self._check_consecutive_dy_positive(dy_list, frame_idx - N + 1, N):
                            if v_list[frame_idx] >= v_q80:
                                current_state = SwingPhase.DOWNSWING
                                phases[frame_idx] = SwingPhase.DOWNSWING
                                print(f"   帧{frame_idx+1}: Transition → Downswing (早触发: dy>0×{N} 且 v≥Q80)")
                                # 关闭窗口并记录结束帧
                                data['transition_end'] = frame_idx
                                self.top_idx = None
                                self.transition_window = None

                # 3) 窗口结束：决定去向（Downswing 或回退 Backswing）
                if frame_idx == win_r:
                    N = self.config['n_down_after_top']
                    if self._check_consecutive_dy_positive(dy_list, self.top_idx + 1, N):
                        current_state = SwingPhase.DOWNSWING
                        print(f"   帧{frame_idx+1}: Transition → Downswing (dy>0 连续 {N})")
                    else:
                        current_state = SwingPhase.BACKSWING
                        print(f"   帧{frame_idx+1}: Transition → Backswing (Top 失败回退)")
                    # 记录窗口结束帧，供后续Downswing安全间隔使用
                    data['transition_end'] = win_r
                    self.top_idx = None
                    self.transition_window = None
            # ---------- Top/Transition 窗口控制逻辑 ----------

            
            # 检查是否需要状态转换
            if result['should_transition']:
                current_state = self._normalize_phase(result.get('next_state'))
                state_start_frame = frame_idx
                print(f"   帧{frame_idx+1}: {result['new_state'].value} → {current_state.value}")
        
        return phases

    def _check_consecutive_dy_positive(self, dy_list: List[float], start_idx: int, count: int) -> bool:
        """检查从 start_idx 开始是否有连续 count 帧 dy>0。"""
        if start_idx >= len(dy_list) - count + 1:
            return False
        c = 0
        for i in range(start_idx, min(start_idx + count, len(dy_list))):
            if dy_list[i] > 0:
                c += 1
            else:
                c = 0
        return c >= count
    
    def _postprocess_phases(self, phases: List[SwingPhase], data: Dict) -> List[SwingPhase]:
        """后处理阶段：优化和验证状态"""
        
        # 1. 注入缺失的Impact
        phases = self._inject_impact_if_missing(phases, data)
        
        # 2. 状态不可逆约束：Impact之后不能回到Downswing
        phases = self._enforce_state_irreversibility(phases)
        
        # 3. 形态学后处理
        phases = self._morphological_post_processing(phases)
        
        # 4. 状态一致性检查
        phases = self._check_state_consistency(phases)
        
        # 5. 物理逻辑验证
        phases = self._validate_physics_logic(phases, data)
        
        return phases

    def _enforce_state_irreversibility(self, phases: List[SwingPhase]) -> List[SwingPhase]:
        """强制状态不可逆：Impact之后进入FollowThrough状态"""
        result = phases.copy()
        impact_found = False
        
        for i, phase in enumerate(result):
            if phase == SwingPhase.IMPACT:
                impact_found = True
                continue
            
            if impact_found:
                if phase == SwingPhase.DOWNSWING:
                    # Impact之后出现Downswing，这是物理上不可能的
                    # 强制进入FollowThrough状态
                    result[i] = SwingPhase.FOLLOWTHROUGH
                    print(f"   帧{i+1}: 强制Downswing→FollowThrough (Impact后状态不可逆)")
        
        return result
    
    def _is_followthrough_candidate(self, frame_idx: int, phases: List[SwingPhase], original_phases: List[SwingPhase]) -> bool:
        """判断帧是否为FollowThrough候选"""
        # 简单的FollowThrough判断：dy < 0 (向上运动) 且 在Impact之后
        if frame_idx >= len(original_phases):
            return False
        
        # 检查是否有dy数据
        if hasattr(self, 'frame_data') and frame_idx < len(self.frame_data):
            dy = self.frame_data[frame_idx].get('dy', 0)
            # 如果dy < 0 (向上运动)，可能是FollowThrough
            return dy < 0
        
        return False
    
    def _inject_impact_if_missing(self, phases: List[SwingPhase], data: Dict) -> List[SwingPhase]:
        """若序列中没有Impact，则在Transition之后的窗口内依据规则检测并插入。"""
        if any(p == SwingPhase.IMPACT for p in phases):
            return phases
        # 寻找最后一个 Transition 段的结束帧
        try:
            last_trans_end = max(i for i, p in enumerate(phases) if p == SwingPhase.TRANSITION)
        except ValueError:
            return phases
        safety = data.get('impact_safety_after_transition', 2)
        start_idx = min(len(phases) - 1, last_trans_end + safety + 1)
        impact_idx = self._detect_impact_candidate(data, start_idx, window=20)
        if impact_idx is None:
            return phases
        # 写入Impact，并将其后的一个短窗口保持Downswing，随后按原逻辑进入FollowThrough（由后续规则决定）
        phases[impact_idx] = SwingPhase.IMPACT
        return phases

    def _detect_impact_candidate(self, data: Dict, start_idx: int, window: int = 20) -> Optional[int]:
        """在 [start_idx, start_idx+window] 内检测Impact候选。
        规则：
          - y 局部极大（最低点）
          - dy 前>0 后<0
          - v ≥ 窗口Q分位（默认Q=0.7）
        返回首选索引或None
        """
        traj = data['trajectory']
        dy_list = data['dy_list']
        v_list = data['v_list']
        q = data.get('impact_v_quantile', 0.7)
        k = data.get('impact_local_window_k', 2)
        n = len(traj)
        L = len(v_list)
        end_idx = min(n - 1, start_idx + window)
        candidates = []
        for i in range(max(1, start_idx), end_idx):
            if i < k or i >= n - k:
                continue
            if traj[i] is None:
                continue
            # dy 前后符号
            # 使用与帧中心对齐的差分：dy[i] 表示 i->i+1，故中心i的“前”为dy[i-1]或dy[i]，
            # 为捕捉从向下(>0)到向上(<0)的过零，采用 dy[i] 与 dy[i+1]
            if i < L - 1:
                dy_before = dy_list[i]
                dy_after = dy_list[i + 1]
            else:
                continue
            direction_switch = (dy_before > 0 and dy_after < 0)
            if not direction_switch:
                continue
            # y 局部极大
            y_center = traj[i][1]
            neighborhood = []
            ok = True
            for j in range(i - k, i + k + 1):
                if traj[j] is None:
                    ok = False
                    break
                neighborhood.append(traj[j][1])
            if not ok:
                continue
            if not all(y_center >= y for y in neighborhood):
                continue
            # v 高分位
            v_win = v_list[max(0, i - 3):min(L, i + 4)]
            if not v_win:
                continue
            v_sorted = sorted(v_win)
            q_idx = int(q * (len(v_sorted) - 1))
            qv = v_sorted[q_idx]
            v_here = v_list[i] if i < L else 0.0
            if v_here < qv:
                continue
            # 得分：更大的y、更大的v优先
            score = y_center * 0.6 + v_here * 0.4
            candidates.append((score, i))
        if not candidates:
            # 回退策略：选取窗口内 y 最大的帧作为 impact 候选（最低点）
            best_i = None
            best_y = -1.0
            for i in range(max(1, start_idx), end_idx):
                if traj[i] is None:
                    continue
                y = traj[i][1]
                if y > best_y:
                    best_y = y
                    best_i = i
            return best_i
        candidates.sort(reverse=True)
        return candidates[0][1]
    
    def _morphological_post_processing(self, phases: List[SwingPhase]) -> List[SwingPhase]:
        """形态学后处理 - 去毛刺和填洞"""
        N = self.config['debounce_frames']
        
        # 开运算：先腐蚀后膨胀，去除小毛刺
        phases = self._erode_phases(phases, N)
        phases = self._dilate_phases(phases, N)
        
        return phases
    
    def _erode_phases(self, phases: List[SwingPhase], window: int) -> List[SwingPhase]:
        """腐蚀操作 - 去除小毛刺"""
        result = phases.copy()
        half_window = window // 2
        
        for i in range(half_window, len(phases) - half_window):
            window_phases = phases[i-half_window:i+half_window+1]
            # 如果窗口内大部分是Unknown，则当前帧也设为Unknown
            unknown_count = sum(1 for p in window_phases if p == SwingPhase.UNKNOWN)
            if unknown_count > len(window_phases) * 0.6:
                result[i] = SwingPhase.UNKNOWN
        
        return result
    
    def _dilate_phases(self, phases: List[SwingPhase], window: int) -> List[SwingPhase]:
        """膨胀操作 - 填充小洞"""
        result = phases.copy()
        half_window = window // 2
        
        for i in range(half_window, len(phases) - half_window):
            if phases[i] == SwingPhase.UNKNOWN:
                window_phases = phases[i-half_window:i+half_window+1]
                # 如果窗口内大部分是某个状态，则填充该状态
                phase_counts = {}
                for p in window_phases:
                    if p != SwingPhase.UNKNOWN:
                        phase_counts[p] = phase_counts.get(p, 0) + 1
                
                if phase_counts:
                    most_common = max(phase_counts.items(), key=lambda x: x[1])
                    if most_common[1] > len(window_phases) * 0.4:
                        result[i] = most_common[0]
        
        return result
    
    def _check_state_consistency(self, phases: List[SwingPhase]) -> List[SwingPhase]:
        """检查状态一致性"""
        # 确保状态转换的合理性
        expected_sequence = [
            SwingPhase.ADDRESS,
            SwingPhase.BACKSWING,
            SwingPhase.TRANSITION,
            SwingPhase.DOWNSWING,
            SwingPhase.IMPACT,
            SwingPhase.FOLLOWTHROUGH,
            SwingPhase.FINISH
        ]
        
        # 这里可以添加更复杂的一致性检查逻辑
        return phases
    
    def _validate_physics_logic(self, phases: List[SwingPhase], data: Dict) -> List[SwingPhase]:
        """物理逻辑验证"""
        # 基于高尔夫挥杆的物理原理验证状态合理性
        # 这里可以添加更多物理约束
        
        return phases
    
    def _print_statistics(self, phases: List[SwingPhase]):
        """打印统计信息"""
        phase_counts = {}
        for phase in phases:
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        print("📈 状态分布统计:")
        for phase, count in phase_counts.items():
            percentage = (count / len(phases)) * 100
            print(f"   {phase.value}: {count}帧 ({percentage:.1f}%)")

def main():
    """测试主函数"""
    # 加载测试数据
    data_file = Path("input_data/golftrainer_complete_output.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trajectory = data['golftrainer_analysis']['club_head_result']['trajectory_points']
    
    # 创建状态机
    state_machine = SwingStateMachine()
    
    # 分析挥杆
    phases = state_machine.analyze_swing(trajectory)
    
    # 输出结果
    print("\n🎯 分析结果:")
    for i, phase in enumerate(phases[:20]):  # 显示前20帧
        print(f"   帧{i+1}: {phase.value}")

if __name__ == "__main__":
    main()
