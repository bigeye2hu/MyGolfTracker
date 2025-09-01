from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import numpy as np
from collections import Counter


class SwingAnalyzer:
    """基于杆头轨迹和姿态数据分析挥杆相位的分析器"""
    
    def __init__(self, trajectory: List[List[float]], video_spec: Dict, poses: Optional[List[str]] = None):
        self.trajectory = trajectory
        self.video_spec = video_spec
        self.num_frames = video_spec["num_frames"]
        self.poses = poses or []
        
    def analyze_swing_phases(self) -> Dict[str, Dict]:
        """
        分析挥杆相位，返回详细的相位信息
        
        Returns:
            Dict with phase information including frame ranges, durations, and key metrics
        """
        if len(self.trajectory) < 10:
            return self._get_default_phases()
        
        # 结合姿态数据识别关键帧
        key_frames = self._identify_key_frames_with_poses()
        
        # 基于轨迹分析补充关键帧
        trajectory_key_frames = self._analyze_trajectory_key_frames()
        
        # 合并和优化关键帧
        combined_key_frames = self._combine_key_frames(key_frames, trajectory_key_frames)
        
        # 构建详细的相位信息
        phases = self._build_detailed_phases(combined_key_frames)
        
        return phases
    
    def _identify_key_frames_with_poses(self) -> Dict[str, int]:
        """基于姿态数据识别关键帧"""
        key_frames = {}
        
        if not self.poses:
            return key_frames
        
        # 寻找姿态转换点
        pose_transitions = self._find_pose_transitions()
        
        # 基于姿态转换识别关键帧
        for transition in pose_transitions:
            frame_idx, from_pose, to_pose = transition
            
            if from_pose.endswith('Start') and to_pose.endswith('Top'):
                key_frames['backswing_start'] = max(0, frame_idx - 5)
                key_frames['top'] = frame_idx
            elif from_pose.endswith('Top') and to_pose.endswith('Finish'):
                key_frames['downswing_start'] = frame_idx
                key_frames['impact_estimated'] = frame_idx + 15  # 估算撞击点
            elif to_pose.endswith('Finish'):
                key_frames['finish'] = frame_idx
        
        # 如果没有明确的转换，基于姿态分布推断
        if not key_frames:
            key_frames = self._infer_from_pose_distribution()
        
        return key_frames
    
    def _find_pose_transitions(self) -> List[Tuple[int, str, str]]:
        """找到姿态转换点"""
        transitions = []
        current_pose = None
        pose_start = 0
        
        for i, pose in enumerate(self.poses):
            if pose != current_pose and pose != "Unknown":
                if current_pose is not None and current_pose != "Unknown":
                    # 发现姿态转换
                    transitions.append((i, current_pose, pose))
                current_pose = pose
                pose_start = i
        
        return transitions
    
    def _infer_from_pose_distribution(self) -> Dict[str, int]:
        """基于姿态分布推断关键帧"""
        key_frames = {}
        pose_counter = Counter(self.poses)
        
        # 找到各姿态的主要出现区间
        start_frames = [i for i, pose in enumerate(self.poses) if pose.endswith('Start')]
        top_frames = [i for i, pose in enumerate(self.poses) if pose.endswith('Top')]
        finish_frames = [i for i, pose in enumerate(self.poses) if pose.endswith('Finish')]
        
        if start_frames:
            key_frames['address'] = min(start_frames)
            key_frames['backswing_start'] = min(start_frames)
        
        if top_frames:
            key_frames['top'] = int(np.median(top_frames))
        
        if finish_frames:
            key_frames['finish'] = int(np.median(finish_frames))
        
        # 基于姿态帧数估算其他关键点
        if 'top' in key_frames and 'finish' in key_frames:
            top_frame = key_frames['top']
            finish_frame = key_frames['finish']
            # 估算撞击点在下杆中期
            key_frames['impact_estimated'] = top_frame + int((finish_frame - top_frame) * 0.6)
        
        return key_frames
    
    def _analyze_trajectory_key_frames(self) -> Dict[str, int]:
        """基于轨迹分析识别关键帧"""
        key_frames = {}
        
        # 计算轨迹特征
        velocities = self._calculate_velocities()
        y_coords = [point[1] for point in self.trajectory if not np.isnan(point[1])]
        
        if len(y_coords) < 10:
            return key_frames
        
        # 找到轨迹的最高点和最低点
        min_y_idx = np.argmin(y_coords)
        max_y_idx = np.argmax(y_coords)
        
        # 最高点通常对应上杆顶点
        key_frames['trajectory_top'] = min_y_idx
        
        # 最低点通常对应撞击点附近
        key_frames['trajectory_impact'] = max_y_idx
        
        # 基于速度变化找关键点
        if len(velocities) > 20:
            # 找到速度的局部最大值（通常在下杆阶段）
            velocity_peaks = self._find_velocity_peaks(velocities)
            if velocity_peaks:
                key_frames['max_velocity'] = velocity_peaks[0]
        
        return key_frames
    
    def _find_velocity_peaks(self, velocities: List[float]) -> List[int]:
        """找到速度峰值"""
        peaks = []
        window_size = 5
        
        for i in range(window_size, len(velocities) - window_size):
            if velocities[i] == max(velocities[i-window_size:i+window_size+1]):
                if velocities[i] > np.mean(velocities) * 1.5:  # 显著高于平均速度
                    peaks.append(i)
        
        return sorted(peaks, key=lambda x: velocities[x], reverse=True)
    
    def _combine_key_frames(self, pose_frames: Dict[str, int], trajectory_frames: Dict[str, int]) -> Dict[str, int]:
        """合并姿态和轨迹关键帧"""
        combined = {}
        
        # 优先使用姿态数据，轨迹数据作为补充
        for key, frame in pose_frames.items():
            combined[key] = frame
        
        # 如果姿态数据缺失某些关键点，使用轨迹数据补充
        if 'top' not in combined and 'trajectory_top' in trajectory_frames:
            combined['top'] = trajectory_frames['trajectory_top']
        
        if 'impact_estimated' not in combined and 'trajectory_impact' in trajectory_frames:
            combined['impact_estimated'] = trajectory_frames['trajectory_impact']
        
        # 确保关键帧的合理性和顺序
        combined = self._validate_key_frames(combined)
        
        return combined
    
    def _validate_key_frames(self, key_frames: Dict[str, int]) -> Dict[str, int]:
        """验证和修正关键帧的合理性"""
        validated = {}
        
        # 确保关键帧在有效范围内
        for key, frame in key_frames.items():
            validated[key] = max(0, min(frame, self.num_frames - 1))
        
        # 确保时序合理性
        frame_order = ['address', 'backswing_start', 'top', 'downswing_start', 'impact_estimated', 'finish']
        prev_frame = 0
        
        for key in frame_order:
            if key in validated:
                if validated[key] < prev_frame:
                    validated[key] = prev_frame + 1
                prev_frame = validated[key]
        
        return validated
    
    def _build_detailed_phases(self, key_frames: Dict[str, int]) -> Dict[str, Dict]:
        """构建详细的相位信息"""
        phases = {}
        
        # 定义相位和对应的关键帧
        phase_definitions = {
            "Address": ("start", "backswing_start"),
            "Backswing": ("backswing_start", "top"),
            "Transition": ("top", "downswing_start"),
            "Downswing": ("downswing_start", "impact_estimated"),
            "Impact": ("impact_estimated", "impact_estimated"),
            "FollowThrough": ("impact_estimated", "finish"),
            "Finish": ("finish", "end")
        }
        
        # 设置默认关键帧
        default_frames = {
            "start": 0,
            "backswing_start": key_frames.get("backswing_start", int(self.num_frames * 0.1)),
            "top": key_frames.get("top", int(self.num_frames * 0.4)),
            "downswing_start": key_frames.get("downswing_start", key_frames.get("top", int(self.num_frames * 0.4))),
            "impact_estimated": key_frames.get("impact_estimated", int(self.num_frames * 0.7)),
            "finish": key_frames.get("finish", int(self.num_frames * 0.9)),
            "end": self.num_frames - 1
        }
        
        # 构建每个相位的详细信息
        for phase_name, (start_key, end_key) in phase_definitions.items():
            start_frame = default_frames[start_key]
            end_frame = default_frames[end_key]
            
            # 确保相位至少有1帧
            if end_frame <= start_frame:
                end_frame = start_frame + 1
            
            duration = end_frame - start_frame
            
            # 计算该相位的轨迹特征
            phase_trajectory = self.trajectory[start_frame:end_frame+1]
            phase_metrics = self._calculate_phase_metrics(phase_trajectory, start_frame, end_frame)
            
            phases[phase_name] = {
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration": duration,
                "duration_seconds": duration / self.video_spec.get("fps", 30),
                **phase_metrics
            }
        
        # 添加关键帧信息
        phases["key_frames"] = default_frames
        
        # 添加整体统计
        phases["summary"] = self._calculate_swing_summary(phases)
        
        return phases
    
    def _calculate_phase_metrics(self, trajectory: List[List[float]], start_frame: int, end_frame: int) -> Dict:
        """计算相位的轨迹指标"""
        if not trajectory:
            return {"distance": 0.0, "avg_velocity": 0.0, "max_velocity": 0.0}
        
        # 过滤有效点
        valid_points = [p for p in trajectory if not (np.isnan(p[0]) or np.isnan(p[1]))]
        
        if len(valid_points) < 2:
            return {"distance": 0.0, "avg_velocity": 0.0, "max_velocity": 0.0}
        
        # 计算总距离
        total_distance = 0.0
        velocities = []
        
        for i in range(len(valid_points) - 1):
            dx = valid_points[i+1][0] - valid_points[i][0]
            dy = valid_points[i+1][1] - valid_points[i][1]
            distance = np.sqrt(dx*dx + dy*dy)
            total_distance += distance
            velocities.append(distance)
        
        return {
            "distance": total_distance,
            "avg_velocity": np.mean(velocities) if velocities else 0.0,
            "max_velocity": np.max(velocities) if velocities else 0.0,
            "velocity_change": np.std(velocities) if velocities else 0.0
        }
    
    def _calculate_swing_summary(self, phases: Dict[str, Dict]) -> Dict:
        """计算挥杆的总体统计"""
        total_duration = sum(phase.get("duration", 0) for phase in phases.values() if isinstance(phase, dict) and "duration" in phase)
        total_distance = sum(phase.get("distance", 0) for phase in phases.values() if isinstance(phase, dict) and "distance" in phase)
        
        return {
            "total_duration_frames": total_duration,
            "total_duration_seconds": total_duration / self.video_spec.get("fps", 30),
            "total_distance": total_distance,
            "avg_swing_velocity": total_distance / max(total_duration, 1) if total_duration > 0 else 0.0
        }
    
    def _calculate_velocities(self) -> List[float]:
        """计算每帧的杆头速度"""
        velocities = [0.0]  # 第一帧速度为0
        
        for i in range(1, len(self.trajectory)):
            if self.trajectory[i] != [0.0, 0.0] and self.trajectory[i-1] != [0.0, 0.0]:
                dx = self.trajectory[i][0] - self.trajectory[i-1][0]
                dy = self.trajectory[i][1] - self.trajectory[i-1][1]
                velocity = np.sqrt(dx*dx + dy*dy)
                velocities.append(velocity)
            else:
                velocities.append(0.0)
                
        return velocities
    
    def _calculate_angles(self) -> List[float]:
        """计算杆头轨迹的角度变化"""
        angles = [0.0]  # 第一帧角度为0
        
        for i in range(2, len(self.trajectory)):
            if (self.trajectory[i] != [0.0, 0.0] and 
                self.trajectory[i-1] != [0.0, 0.0] and 
                self.trajectory[i-2] != [0.0, 0.0]):
                
                # 计算三个连续点形成的角度
                p1 = np.array(self.trajectory[i-2])
                p2 = np.array(self.trajectory[i-1])
                p3 = np.array(self.trajectory[i])
                
                v1 = p2 - p1
                v2 = p3 - p2
                
                if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle = np.arccos(cos_angle) * 180 / np.pi
                    angles.append(angle)
                else:
                    angles.append(0.0)
            else:
                angles.append(0.0)
                
        angles.append(0.0)  # 最后一帧角度为0
        return angles
    
    def _identify_key_frames(self, velocities: List[float], angles: List[float]) -> Dict[str, int]:
        """识别关键帧"""
        key_frames = {}
        
        # 找到速度峰值（上杆顶点）
        if len(velocities) > 10:
            # 使用滑动窗口找到局部最大值
            window_size = 5
            peak_frames = []
            for i in range(window_size, len(velocities) - window_size):
                if velocities[i] == max(velocities[i-window_size:i+window_size+1]):
                    peak_frames.append(i)
            
            if peak_frames:
                # 选择最明显的峰值作为上杆顶点
                top_frame = max(peak_frames, key=lambda x: velocities[x])
                key_frames["top"] = top_frame
                
                # 基于上杆顶点推断其他关键帧
                key_frames["address"] = max(0, top_frame - 20)
                key_frames["transition"] = top_frame
                key_frames["impact"] = min(len(velocities) - 1, top_frame + 25)
                key_frames["finish"] = min(len(velocities) - 1, top_frame + 50)
        
        return key_frames
    
    def _build_phases(self, key_frames: Dict[str, int]) -> Dict[str, List[int]]:
        """构建挥杆相位"""
        phases = {
            "Address": [0, 0],
            "Backswing": [0, 0],
            "Transition": [0, 0],
            "Downswing": [0, 0],
            "Impact": [0, 0],
            "FollowThrough": [0, 0],
            "Finish": [0, 0]
        }
        
        if "address" in key_frames and "top" in key_frames:
            phases["Address"] = [0, key_frames["address"]]
            phases["Backswing"] = [key_frames["address"], key_frames["top"]]
            phases["Transition"] = [key_frames["top"], key_frames["top"]]
            
        if "top" in key_frames and "impact" in key_frames:
            phases["Downswing"] = [key_frames["top"], key_frames["impact"]]
            phases["Impact"] = [key_frames["impact"], key_frames["impact"]]
            
        if "impact" in key_frames and "finish" in key_frames:
            phases["FollowThrough"] = [key_frames["impact"], key_frames["finish"]]
            phases["Finish"] = [key_frames["finish"], self.num_frames - 1]
            
        return phases
    
    def _get_default_phases(self) -> Dict[str, Dict]:
        """返回默认相位（当轨迹数据不足时）"""
        default_phases = {}
        phase_names = ["Address", "Backswing", "Transition", "Downswing", "Impact", "FollowThrough", "Finish"]
        
        for phase_name in phase_names:
            default_phases[phase_name] = {
                "start_frame": 0,
                "end_frame": 0,
                "duration": 0,
                "duration_seconds": 0.0,
                "distance": 0.0,
                "avg_velocity": 0.0,
                "max_velocity": 0.0,
                "velocity_change": 0.0
            }
        
        default_phases["key_frames"] = {
            "start": 0,
            "backswing_start": 0,
            "top": 0,
            "downswing_start": 0,
            "impact_estimated": 0,
            "finish": 0,
            "end": 0
        }
        
        default_phases["summary"] = {
            "total_duration_frames": 0,
            "total_duration_seconds": 0.0,
            "total_distance": 0.0,
            "avg_swing_velocity": 0.0
        }
        
        return default_phases
