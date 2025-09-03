from __future__ import annotations

from typing import Generator, Tuple

import cv2


def iter_video_frames(path: str, sample_stride: int = 1, max_size: int = 960) -> Generator[Tuple[bool, "np.ndarray"], None, None]:
    """Yield frames with optional downscale and frame sampling.

    - sample_stride: >1 means pick 1 frame every N frames
    - max_size: resize so that the longer edge <= max_size
    """
    cap = cv2.VideoCapture(path)
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if sample_stride > 1 and (idx % sample_stride) != 0:
                idx += 1
                continue
            h, w = frame.shape[:2]
            long_edge = max(h, w)
            if max_size and long_edge > max_size:
                scale = float(max_size) / float(long_edge)
                new_w = int(w * scale)
                new_h = int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))
            yield True, frame
            idx += 1
    finally:
        cap.release()


