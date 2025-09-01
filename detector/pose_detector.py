from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import numpy as np
import mediapipe as mp
import cv2


class PoseDetector:
    """使用 MediaPipe 检测人体姿态，识别挥杆姿势"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 定义关键关节点索引
        self.KEYPOINTS = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26,
            'left_ankle': 27,
            'right_ankle': 28
        }
        
    def detect_pose(self, frame_bgr: np.ndarray) -> Optional[mp.solutions.pose.PoseLandmark]:
        """检测单帧的姿态"""
        # 转换为 RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        return results.pose_landmarks if results.pose_landmarks else None
    
    def classify_golf_pose(self, landmarks: mp.solutions.pose.PoseLandmark, handed: str = "right") -> str:
        """
        基于关键点位置分类挥杆姿势
        
        Args:
            landmarks: MediaPipe 姿态关键点
            handed: 左右手 ("right" 或 "left")
            
        Returns:
            挥杆姿势: "RhStart", "RhTop", "RhFinish", "LhStart", "LhTop", "LhFinish", "Unknown"
        """
        if not landmarks:
            return "Unknown"
            
        # 获取关键点坐标
        keypoints = {}
        for name, idx in self.KEYPOINTS.items():
            landmark = landmarks.landmark[idx]
            keypoints[name] = (landmark.x, landmark.y, landmark.visibility)
        
        # 检查关键点可见性
        if not self._check_visibility(keypoints):
            return "Unknown"
        
        # 基于左右手判断使用哪一侧的关键点
        if handed.lower() == "right":
            return self._classify_right_handed_pose(keypoints)
        else:
            return self._classify_left_handed_pose(keypoints)
    
    def _check_visibility(self, keypoints: Dict[str, Tuple[float, float, float]]) -> bool:
        """检查关键点是否足够可见"""
        min_visibility = 0.5
        required_points = ['right_shoulder', 'right_elbow', 'right_wrist', 'right_hip']
        
        for point in required_points:
            if point in keypoints and keypoints[point][2] < min_visibility:
                return False
        return True
    
    def _classify_right_handed_pose(self, keypoints: Dict[str, Tuple[float, float, float]]) -> str:
        """分类右手挥杆姿势"""
        # 获取右侧关键点
        shoulder = keypoints.get('right_shoulder', (0, 0, 0))
        elbow = keypoints.get('right_elbow', (0, 0, 0))
        wrist = keypoints.get('right_wrist', (0, 0, 0))
        hip = keypoints.get('right_hip', (0, 0, 0))
        
        # 计算手臂角度
        arm_angle = self._calculate_arm_angle(shoulder, elbow, wrist)
        
        # 基于手臂角度和位置分类
        if arm_angle < 45:  # 手臂下垂
            return "RhStart"
        elif arm_angle > 135:  # 手臂高举
            return "RhTop"
        elif arm_angle < 90:  # 手臂下摆
            return "RhFinish"
        else:
            return "RhStart"  # 默认起始姿势
    
    def _classify_left_handed_pose(self, keypoints: Dict[str, Tuple[float, float, float]]) -> str:
        """分类左手挥杆姿势"""
        # 获取左侧关键点
        shoulder = keypoints.get('left_shoulder', (0, 0, 0))
        elbow = keypoints.get('left_elbow', (0, 0, 0))
        wrist = keypoints.get('left_wrist', (0, 0, 0))
        hip = keypoints.get('left_hip', (0, 0, 0))
        
        # 计算手臂角度
        arm_angle = self._calculate_arm_angle(shoulder, elbow, wrist)
        
        # 基于手臂角度和位置分类
        if arm_angle < 45:  # 手臂下垂
            return "LhStart"
        elif arm_angle > 135:  # 手臂高举
            return "LhTop"
        elif arm_angle < 90:  # 手臂下摆
            return "LhFinish"
        else:
            return "LhStart"  # 默认起始姿势
    
    def _calculate_arm_angle(self, shoulder: Tuple[float, float, float], 
                           elbow: Tuple[float, float, float], 
                           wrist: Tuple[float, float, float]) -> float:
        """计算手臂角度（肩-肘-腕）"""
        # 计算向量
        v1 = np.array([elbow[0] - shoulder[0], elbow[1] - shoulder[1]])
        v2 = np.array([wrist[0] - elbow[0], wrist[1] - elbow[1]])
        
        # 计算角度
        if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle) * 180 / np.pi
            return angle
        return 0.0
    
    def get_landmarks_flat(self, landmarks: mp.solutions.pose.PoseLandmark) -> List[float]:
        """将 MediaPipe 关键点转换为扁平数组"""
        if not landmarks:
            return []
        
        flat_landmarks = []
        for landmark in landmarks.landmark:
            flat_landmarks.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])
        
        return flat_landmarks
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'pose'):
            self.pose.close()
