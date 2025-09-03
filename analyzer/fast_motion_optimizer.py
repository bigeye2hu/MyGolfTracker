from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np
from scipy import signal
from scipy.signal import savgol_filter


class FastMotionOptimizer:
    """专门处理快速移动场景的轨迹优化器"""
    
    def __init__(self, confidence_threshold: float = 0.3, velocity_threshold: float = 0.15):
        self.confidence_threshold = confidence_threshold
        self.velocity_threshold = velocity_threshold
        
    def optimize_trajectory(self, 
                          raw_trajectory: List[List[float]], 
                          confidences: Optional[List[float]] = None) -> Tuple[List[List[float]], List[float]]:
        """
        优化快速移动场景的轨迹数据
        
        Args:
            raw_trajectory: 原始轨迹 [[x, y], ...]
            confidences: 置信度列表（可选）
            
        Returns:
            (优化后的轨迹, 质量评分列表)
        """
        if len(raw_trajectory) < 3:
            return raw_trajectory, [1.0] * len(raw_trajectory)
        
        # 1. 数据预处理
        trajectory = self._preprocess_trajectory(raw_trajectory)
        
        # 2. 检测快速移动区域
        fast_motion_regions = self._detect_fast_motion_regions(trajectory)
        
        # 3. 针对快速移动区域进行特殊处理
        trajectory = self._handle_fast_motion_regions(trajectory, fast_motion_regions, confidences)
        
        # 4. 应用自适应平滑
        trajectory = self._apply_adaptive_smoothing(trajectory, fast_motion_regions)
        
        # 5. 计算质量评分
        quality_scores = self._calculate_quality_scores(trajectory, raw_trajectory, confidences)
        
        return trajectory, quality_scores
    
    def _preprocess_trajectory(self, raw_trajectory: List[List[float]]) -> List[List[float]]:
        """预处理轨迹数据"""
        trajectory = []
        for point in raw_trajectory:
            if len(point) >= 2:
                x, y = point[0], point[1]
                if x == 0.0 and y == 0.0:
                    trajectory.append([np.nan, np.nan])
                elif 0 <= x <= 1 and 0 <= y <= 1:
                    trajectory.append([float(x), float(y)])
                else:
                    trajectory.append([np.nan, np.nan])
            else:
                trajectory.append([np.nan, np.nan])
        return trajectory
    
    def _detect_fast_motion_regions(self, trajectory: List[List[float]]) -> List[bool]:
        """检测快速移动区域"""
        if len(trajectory) < 3:
            return [False] * len(trajectory)
        
        fast_motion = [False] * len(trajectory)
        
        for i in range(1, len(trajectory) - 1):
            if (not np.isnan(trajectory[i-1][0]) and 
                not np.isnan(trajectory[i][0]) and 
                not np.isnan(trajectory[i+1][0])):
                
                # 计算前后帧的速度
                v1 = self._calculate_velocity(trajectory[i-1], trajectory[i])
                v2 = self._calculate_velocity(trajectory[i], trajectory[i+1])
                
                # 如果速度超过阈值，标记为快速移动
                if v1 > self.velocity_threshold or v2 > self.velocity_threshold:
                    fast_motion[i] = True
        
        return fast_motion
    
    def _calculate_velocity(self, point1: List[float], point2: List[float]) -> float:
        """计算两点间的速度（归一化距离）"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return np.sqrt(dx*dx + dy*dy)
    
    def _handle_fast_motion_regions(self, 
                                  trajectory: List[List[float]], 
                                  fast_motion_regions: List[bool],
                                  confidences: Optional[List[float]]) -> List[List[float]]:
        """处理快速移动区域"""
        optimized_trajectory = trajectory.copy()
        
        for i, is_fast_motion in enumerate(fast_motion_regions):
            if is_fast_motion and not np.isnan(trajectory[i][0]):
                # 对于快速移动区域，检查置信度
                if confidences and i < len(confidences):
                    confidence = confidences[i]
                    
                    # 如果置信度较低，尝试使用运动预测
                    if confidence < self.confidence_threshold:
                        predicted_point = self._predict_motion(trajectory, i)
                        if predicted_point is not None:
                            optimized_trajectory[i] = predicted_point
        
        return optimized_trajectory
    
    def _predict_motion(self, trajectory: List[List[float]], index: int) -> Optional[List[float]]:
        """基于运动历史预测当前位置"""
        if index < 2 or index >= len(trajectory) - 1:
            return None
        
        # 获取前两帧的位置
        prev1 = trajectory[index - 1]
        prev2 = trajectory[index - 2]
        
        if (np.isnan(prev1[0]) or np.isnan(prev2[0])):
            return None
        
        # 计算运动向量
        dx = prev1[0] - prev2[0]
        dy = prev1[1] - prev2[1]
        
        # 预测当前位置
        predicted_x = prev1[0] + dx
        predicted_y = prev1[1] + dy
        
        # 确保预测值在有效范围内
        predicted_x = max(0.0, min(1.0, predicted_x))
        predicted_y = max(0.0, min(1.0, predicted_y))
        
        return [predicted_x, predicted_y]
    
    def _apply_adaptive_smoothing(self, 
                                trajectory: List[List[float]], 
                                fast_motion_regions: List[bool]) -> List[List[float]]:
        """应用自适应平滑"""
        if len(trajectory) < 5:
            return trajectory
        
        smoothed_trajectory = trajectory.copy()
        
        for i in range(2, len(trajectory) - 2):
            if not np.isnan(trajectory[i][0]):
                # 根据是否为快速移动区域选择不同的平滑策略
                if fast_motion_regions[i]:
                    # 快速移动区域：使用较小的窗口进行轻度平滑
                    smoothed_trajectory[i] = self._light_smoothing(trajectory, i, window_size=3)
                else:
                    # 正常区域：使用标准平滑
                    smoothed_trajectory[i] = self._standard_smoothing(trajectory, i, window_size=5)
        
        return smoothed_trajectory
    
    def _light_smoothing(self, trajectory: List[List[float]], index: int, window_size: int = 3) -> List[float]:
        """轻度平滑，保持快速移动的特征"""
        half_window = window_size // 2
        start_idx = max(0, index - half_window)
        end_idx = min(len(trajectory), index + half_window + 1)
        
        x_sum = y_sum = count = 0
        for i in range(start_idx, end_idx):
            if not np.isnan(trajectory[i][0]):
                # 给中心点更高权重
                weight = 2.0 if i == index else 1.0
                x_sum += trajectory[i][0] * weight
                y_sum += trajectory[i][1] * weight
                count += weight
        
        if count > 0:
            return [x_sum / count, y_sum / count]
        else:
            return trajectory[index]
    
    def _standard_smoothing(self, trajectory: List[List[float]], index: int, window_size: int = 5) -> List[float]:
        """标准平滑"""
        half_window = window_size // 2
        start_idx = max(0, index - half_window)
        end_idx = min(len(trajectory), index + half_window + 1)
        
        x_sum = y_sum = count = 0
        for i in range(start_idx, end_idx):
            if not np.isnan(trajectory[i][0]):
                x_sum += trajectory[i][0]
                y_sum += trajectory[i][1]
                count += 1
        
        if count > 0:
            return [x_sum / count, y_sum / count]
        else:
            return trajectory[index]
    
    def _calculate_quality_scores(self, 
                                optimized_trajectory: List[List[float]], 
                                raw_trajectory: List[List[float]],
                                confidences: Optional[List[float]]) -> List[float]:
        """计算质量评分"""
        scores = []
        
        for i, (opt_point, raw_point) in enumerate(zip(optimized_trajectory, raw_trajectory)):
            score = 1.0
            
            # 1. 检查原始数据质量
            if raw_point == [0.0, 0.0]:
                score *= 0.3
            elif confidences and i < len(confidences):
                # 根据置信度调整评分
                confidence = confidences[i]
                if confidence < 0.3:
                    score *= 0.5  # 低置信度
                elif confidence < 0.6:
                    score *= 0.8  # 中等置信度
            
            # 2. 检查轨迹连续性
            if i > 0 and i < len(optimized_trajectory) - 1:
                prev_point = optimized_trajectory[i-1]
                next_point = optimized_trajectory[i+1]
                
                if (not np.isnan(prev_point[0]) and 
                    not np.isnan(next_point[0]) and 
                    not np.isnan(opt_point[0])):
                    
                    # 计算速度变化
                    v1 = self._calculate_velocity(prev_point, opt_point)
                    v2 = self._calculate_velocity(opt_point, next_point)
                    
                    # 速度变化过大则降低评分
                    if abs(v1 - v2) > 0.2:
                        score *= 0.7
            
            scores.append(score)
        
        return scores
