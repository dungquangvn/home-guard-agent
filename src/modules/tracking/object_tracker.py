import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment


def iou(bbox1, bbox2):
    """Compute IoU between two bounding boxes: (x, y, w, h)"""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    inter_area = max(0, xb - xa) * max(0, yb - ya)
    area1 = w1 * h1
    area2 = w2 * h2

    union_area = area1 + area2 - inter_area
    if union_area == 0:
        return 0.0

    return inter_area / union_area


@dataclass
class Track:
    tracker_id: int
    bbox: Tuple[int, int, int, int]


class ObjectTracker:
    def __init__(self, iou_threshold=0.3):
        """
        iou_threshold: độ tương đồng để coi như là cùng object
        """
        self.next_id = 1
        self.iou_threshold = iou_threshold
        self.tracks: Dict[int, Track] = {}

    def update(self, detections: List):
        """
        detections: danh sách Detection (bbox + type)
        """

        if len(self.tracks) == 0:
            # Không có track nào → tạo mới cho tất cả detections
            for det in detections:
                det.tracker_id = self.next_id
                self.tracks[self.next_id] = Track(self.next_id, det.bbox)
                self.next_id += 1
            return detections

        # === Tạo cost matrix dựa trên IOU ===
        track_ids = list(self.tracks.keys())
        cost_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)

        for i, tid in enumerate(track_ids):
            for j, det in enumerate(detections):
                box_old = self.tracks[tid].bbox
                box_new = det.bbox
                cost_matrix[i, j] = 1 - iou(box_old, box_new)  # hungarian là cost → càng nhỏ càng tốt

        # Hungarian matching
        row_idx, col_idx = linear_sum_assignment(cost_matrix)

        matched_tracks = set()
        matched_detections = set()

        # Gán detection vào track nếu IOU đủ lớn
        for r, c in zip(row_idx, col_idx):
            track_id = track_ids[r]
            det = detections[c]

            if 1 - cost_matrix[r, c] < self.iou_threshold:
                continue  # skip match yếu

            # Match hợp lệ
            self.tracks[track_id].bbox = det.bbox
            self.tracks[track_id].lost_frames = 0
            det.tracker_id = track_id

            matched_tracks.add(track_id)
            matched_detections.add(c)

        # Unmatched tracks: tăng lost_frames
        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].lost_frames += 1

        # Xóa track đã mất dấu
        for tid in list(self.tracks.keys()):
            del self.tracks[tid]

        # Unmatched detections: tạo track mới
        for idx, det in enumerate(detections):
            if idx not in matched_detections:
                det.tracker_id = self.next_id
                self.tracks[self.next_id] = Track(self.next_id, det.bbox)
                self.next_id += 1

        return detections
