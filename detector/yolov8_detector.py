from __future__ import annotations

from typing import List, Optional, Tuple

import os
import cv2

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

            # 始终在 CPU 上加载，避免无 GPU 环境导致的开销与不确定行为
            model = YOLO(self.model_path)
            try:
                # 将模型固定在 CPU，关闭 half 精度
                model.to("cpu")
                if hasattr(model, "model") and hasattr(model.model, "half"):
                    model.model.half = False
            except Exception:
                # 兼容不同版本的 ultralytics
                pass
            YOLOv8Detector._model = model

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

        # CPU增强模式：允许更多线程并行处理
        try:
            cv2.setNumThreads(4)  # 增加OpenCV线程数
            if hasattr(cv2, "ocl"):
                cv2.ocl.setUseOpenCL(True)  # 启用OpenCL加速
        except Exception:
            pass
        for k in [
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", 
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ]:
            os.environ.setdefault(k, "4")  # 增加BLAS线程数

        # 控制推理分辨率并固定在 CPU 上推理，减少 CPU 机器上的负载
        # 使用动态分辨率以平衡检测精度和处理速度
        results = YOLOv8Detector._model.predict(
            source=image_bgr,
            verbose=False,
            device="cpu",
            imgsz=imgsz,  # 使用传入的分辨率参数
            conf=conf,  # 使用传入的置信度阈值
            iou=iou,  # 使用传入的IoU阈值
            max_det=max_det,  # 使用传入的最大检测数量
            agnostic_nms=False,  # 使用类别感知的NMS
            augment=False,  # 关闭测试时增强以提高速度
        )
        if not results:
            return None

        r0 = results[0]
        if r0.boxes is None or r0.boxes.data is None or len(r0.boxes.data) == 0:
            return None

        # boxes: [x1, y1, x2, y2, conf, cls]
        boxes = r0.boxes.data.cpu().numpy()
        names = getattr(r0, "names", {})
        
        if debug:
            print(f"🔍 检测到 {len(boxes)} 个目标:")
            for i, box in enumerate(boxes):
                x1, y1, x2, y2, conf, cls = box
                cls_id = int(cls)
                cls_name = names.get(cls_id, f"unknown_{cls_id}")
                print(f"  {i+1}. {cls_name} (ID:{cls_id}) - 置信度: {conf:.3f} - 位置: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
        
        # 改进的杆头检测逻辑：严格只选择杆头，拒绝回退到其他类别
        club_head_boxes = None
        
        # 1. 首先尝试通过类别名称匹配杆头
        try:
            if isinstance(names, dict):
                head_class_ids = [cid for cid, n in names.items() if str(n).lower() in ("club_head", "clubhead", "head")]
                if head_class_ids:
                    club_head_boxes = boxes[np.isin(boxes[:, 5], head_class_ids)]
                    if debug:
                        print(f"🎯 通过名称匹配找到杆头类别ID: {head_class_ids}")
        except Exception:
            pass
        
        # 2. 如果名称匹配失败，尝试通过ID匹配（严格只匹配杆头ID=1）
        if club_head_boxes is None or len(club_head_boxes) == 0:
            club_head_boxes = boxes[boxes[:, 5] == 1]  # 只匹配ID=1的杆头
            if debug:
                print(f"🎯 通过ID匹配找到杆头检测框: {len(club_head_boxes)} 个")
        
        # 3. 如果没有找到杆头检测，直接返回None（不使用回退策略）
        if len(club_head_boxes) == 0:
            if debug:
                print("❌ 没有检测到杆头，返回None（禁用杆身/手部回退策略）")
                
                # 显示所有检测到的目标供调试
                all_boxes = boxes
                if len(all_boxes) > 0:
                    print("🔍 当前帧检测到的所有目标:")
                    for i, box in enumerate(all_boxes):
                        x1, y1, x2, y2, conf, cls = box
                        cls_id = int(cls)
                        cls_name = names.get(cls_id, f"unknown_{cls_id}")
                        print(f"  {i+1}. {cls_name} (ID:{cls_id}) - 置信度: {conf:.3f}")
            
            return None
        
        # 4. 在杆头检测结果中选择最佳检测框
        # 优先选择置信度最高的，如果置信度相近则选择面积较大的
        best_idx = 0
        best_score = 0
        
        for i, box in enumerate(club_head_boxes):
            x1, y1, x2, y2, conf, cls = box
            area = (x2 - x1) * (y2 - y1)
            
            # 计算综合得分：置信度 + 面积权重
            # 面积太小可能是误检，给予惩罚
            area_penalty = 1.0 if area > 100 else 0.8  # 面积小于100像素时降低权重
            score = conf * area_penalty
            
            if score > best_score:
                best_score = score
                best_idx = i
        
        x1, y1, x2, y2, conf, cls = club_head_boxes[best_idx]
        cls_id = int(cls)
        cls_name = names.get(cls_id, f"unknown_{cls_id}")
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        
        # 如果检测框太小，降低置信度
        area = (x2 - x1) * (y2 - y1)
        if area < 100:
            conf *= 0.8
        
        if debug:
            print(f"✅ 选择最佳杆头: {cls_name} (ID:{cls_id}) - 置信度: {conf:.3f} - 面积: {area:.1f}")
            
            # 检查是否有其他高置信度的检测（仅用于信息显示）
            other_boxes = boxes[boxes[:, 5] != 1]  # 非杆头检测
            if len(other_boxes) > 0:
                best_other_idx = int(np.argmax(other_boxes[:, 4]))
                other_conf = other_boxes[best_other_idx, 4]
                other_cls = int(other_boxes[best_other_idx, 5])
                other_name = names.get(other_cls, f"unknown_{other_cls}")
                
                if other_conf > conf * 1.5:  # 其他检测置信度明显更高
                    print(f"ℹ️  信息: {other_name}置信度({other_conf:.3f})高于杆头({conf:.3f})，但仍优先使用杆头")
        
        return safe_float(cx), safe_float(cy), safe_float(conf)
