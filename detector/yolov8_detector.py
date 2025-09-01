from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from analyzer.config import MODEL_PATH


class YOLOv8Detector:
    """Lazy-load YOLOv8 model and run inference on numpy images."""

    _model = None

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or MODEL_PATH

    def _ensure_model(self) -> None:
        if YOLOv8Detector._model is None:
            from ultralytics import YOLO  # Lazy import

            YOLOv8Detector._model = YOLO(self.model_path)

    def detect_single_point(self, image_bgr: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """
        Run detection on one frame and return the highest-confidence club head bbox center.
        
        Only detects club_head (class 1), filters out club (杆身) and hand (手).

        Returns:
            (cx, cy, conf) if club head detection found, else None
        """
        self._ensure_model()

        results = YOLOv8Detector._model.predict(source=image_bgr, verbose=False)
        if not results:
            return None

        r0 = results[0]
        if r0.boxes is None or r0.boxes.data is None or len(r0.boxes.data) == 0:
            return None

        # boxes: [x1, y1, x2, y2, conf, cls]
        boxes = r0.boxes.data.cpu().numpy()
        
        # 只检测杆头 (class 1: club_head)
        club_head_boxes = boxes[boxes[:, 5] == 1]  # 过滤出杆头类别
        
        if len(club_head_boxes) == 0:
            return None
        
        # 在杆头检测结果中选择置信度最高的
        best_idx = int(np.argmax(club_head_boxes[:, 4]))
        x1, y1, x2, y2, conf = club_head_boxes[best_idx, 0:5]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        return float(cx), float(cy), float(conf)
