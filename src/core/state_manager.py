import time
from src.utils.classes import Detection
from typing import Dict

class StateManager:
    def __init__(self):
        # track_id -> Detection
        self.objects = {}
        
    def update(self, detection: Detection):
        tid = detection.tracker_id
        if tid in self.objects:
            self.objects[tid] = detection
        
    def get_current_detections(self) -> Dict:
        return self.objects

    def update_object(self, det: Detection) -> list:
        '''
        Hàm dùng cho mỗi object phát hiện được trong frame hiện tại.
        Trả về list các events phát hiện được từ object này (phủ trường 
        hợp object mới/object cũ vẫn đang xuất hiện/object đứng lâu).
        '''
        now = time.time()
        events = []

        tid = det.tracker_id

        if tid not in self.objects:
            # Object mới
            det.first_seen = now
            det.last_seen = now
            det.is_recognized = False
            det.is_processing = False

            self.objects[tid] = det

            # emit event
            if det.type == "person":
                events.append({
                    "event": "new_person",
                    "data": det
                })

            if det.type in ["car", "motorcycle", "bicycle"]:
                events.append({
                    "event": "new_vehicle",
                    "data": det
                })

        else:
            # Object cũ
            existing = self.objects[tid]

            existing.last_seen = now
            existing.bbox = det.bbox

            # check đứng lâu
            if det.type == "person":
                duration = now - existing.first_seen
                if duration >= 30:
                    events.append({
                        "event": "stranger_over_30_seconds",
                        "data": existing
                    })

        return events

    def detect_left_objects(self, current_track_ids) -> list:
        '''
        Hàm dùng cho mỗi frame để phát hiện các object đã rời đi
        (Phủ trường hợp object cũ không còn xuất hiện).
        '''
        events = []
        to_remove = []

        for tid, det in self.objects.items():
            if tid not in current_track_ids:
                events.append({
                    "event": "object_left",
                    "data": det
                })
                to_remove.append(tid)

        for tid in to_remove:
            del self.objects[tid]

        return events
