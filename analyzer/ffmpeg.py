from __future__ import annotations

from typing import Generator, Tuple

import cv2


def iter_video_frames(path: str) -> Generator[Tuple[bool, "np.ndarray"], None, None]:
    """Yield frames using OpenCV (ffmpeg backend)."""
    cap = cv2.VideoCapture(path)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield True, frame
    finally:
        cap.release()


