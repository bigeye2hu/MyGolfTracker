from __future__ import annotations

from typing import List, Optional, Tuple

import os
import cv2

import numpy as np

from analyzer.config import MODEL_PATH


class YOLOv8DetectorGPU:
    """GPU-optimized YOLOv8 model for faster inference."""

    _model = None

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or MODEL_PATH

    def _ensure_model(self) -> None:
        if YOLOv8DetectorGPU._model is None:
            from ultralytics import YOLO  # Lazy import

            # 在 GPU 上加载模型
            model = YOLO(self.model_path)
            try:
                # 将模型移动到 GPU，启用 half 精度以提升速度
                model.to("cuda")
                if hasattr(model, "model") and hasattr(model.model, "half"):
                    model.model.half = True  # 启用半精度推理
            except Exception as e:
                print(f"GPU初始化失败，回退到CPU: {e}")
                # 如果GPU不可用，回退到CPU
                model.to("cpu")
                if hasattr(model, "model") and hasattr(model.model, "half"):
                    model.model.half = False
            YOLOv8DetectorGPU._model = model

    def detect_single_point(self, image_bgr: np.ndarray, debug: bool = False, imgsz: int = 480, conf: float = 0.01, iou: float = 0.7, max_det: int = 10) -> Optional[Tuple[float, float, float]]:
        """
        Run detection on one frame and return the highest-confidence club head bbox center.
        
        Only detects club_head (class 1), filters out club (杆身) and hand (手).

        Returns:
            (cx, cy, conf) if club head detection found, else None
        """
        # 定义安全浮点数转换函数
        def safe_float(value):
            """确保浮点数值是JSON兼容的"""
            if value is None or (isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf'))):
                return 0.0
            return float(value)
        
        self._ensure_model()

        # GPU优化模式：减少CPU-GPU数据传输
        try:
            cv2.setNumThreads(2)  # 减少OpenCV线程数，避免与GPU竞争
            if hasattr(cv2, "ocl"):
                cv2.ocl.setUseOpenCL(False)  # 关闭OpenCL，使用GPU
        except Exception:
            pass

        # 控制推理分辨率并在 GPU 上推理
        try:
            results = YOLOv8DetectorGPU._model.predict(
                source=image_bgr,
                verbose=False,
                device="cuda",  # 使用GPU
                imgsz=imgsz,  # 使用传入的分辨率参数
                conf=conf,  # 使用传入的置信度阈值
                iou=iou,  # 使用传入的IoU阈值
                max_det=max_det,  # 使用传入的最大检测数量
                agnostic_nms=False,  # 使用类别感知的NMS
                augment=False,  # 关闭测试时增强以提高速度
                half=True,  # 启用半精度推理
            )
        except Exception as e:
            print(f"GPU推理失败，回退到CPU: {e}")
            # 如果GPU推理失败，回退到CPU
            results = YOLOv8DetectorGPU._model.predict(
                source=image_bgr,
                verbose=False,
                device="cpu",
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                max_det=max_det,
                agnostic_nms=False,
                augment=False,
                half=False,
            )

        if not results:
            return None

        r0 = results[0]
        if r0.boxes is None or len(r0.boxes) == 0:
            return None

        # 获取所有检测结果
        boxes = r0.boxes
        confidences = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()

        # 优先检测杆头 (class 1)
        club_head_detections = []
        for i, (conf, cls, box) in enumerate(zip(confidences, classes, xyxy)):
            if int(cls) == 1:  # 杆头
                x1, y1, x2, y2 = box
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                club_head_detections.append((cx, cy, conf))

        # 如果检测到杆头，返回置信度最高的
        if club_head_detections:
            # 按置信度排序，返回最高的
            club_head_detections.sort(key=lambda x: x[2], reverse=True)
            cx, cy, conf = club_head_detections[0]
            return (safe_float(cx), safe_float(cy), safe_float(conf))

        # 如果没有检测到杆头，检查杆身 (class 0)，但要求更高置信度
        club_detections = []
        for i, (conf, cls, box) in enumerate(zip(confidences, classes, xyxy)):
            if int(cls) == 0 and conf > 0.1:  # 杆身，置信度要求更高
                x1, y1, x2, y2 = box
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                club_detections.append((cx, cy, conf))

        if club_detections:
            # 按置信度排序，返回最高的
            club_detections.sort(key=lambda x: x[2], reverse=True)
            cx, cy, conf = club_detections[0]
            return (safe_float(cx), safe_float(cy), safe_float(conf))

        return None

