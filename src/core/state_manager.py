import time
from src.utils.classes import Detection
from typing import Dict
from src.utils.get_audio_length import get_audio_length
from src.modules.logging.logger import Logger

RECOGNITION_RETRY_INTERVAL = 5.0
MAX_RETRY = 3
CONFIDENCE_THRESHOLD = 0.6

class StateManager:
    def __init__(self, logger: Logger):
        
        self.logger = logger
        
        # track_id -> Detection
        self.objects = {}
        
        # track_id -> is_stranger
        self.has_marked_track_id_as_stranger = {}
    
        # event_name -> timestamp
        self.last_event_called_time = {}
        
        self.alert_audio_length = get_audio_length('data/loud_alarm.wav')
        
    def update(self, detection: Detection):
        '''
        Cập nhật thông tin của một object đã được nhận diện.
        '''
        tid = detection.tracker_id
        
        if tid in self.objects:
            self.objects[tid] = detection
        
    def get_current_detections(self) -> Dict:
        '''
        Lấy tất cả các object hiện có trong state manager.
        '''
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
            det.is_processing = True

            self.objects[tid] = det
            self.has_marked_track_id_as_stranger[tid] = True

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

            # Detect stranger mới
            if existing.is_strange and self.has_marked_track_id_as_stranger.get(tid, True):
                self.has_marked_track_id_as_stranger[tid] = False
                events.append({
                    "event": "is_stranger",
                    "data": existing
                })
                
            # check người lạ đứng lâu mà không có người quen trong nhà
            if existing.type == "person":
                if existing.is_strange:
                    duration = now - existing.first_seen
                    if self.is_any_known_person():
                        existing.first_seen = now
                    if duration >= 5 and self._can_emit('stranger_stay_long', self.alert_audio_length) and not self.is_any_known_person():
                        events.append({
                            "event": "stranger_stay_long",
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
    
    def _can_emit(self, event_name, cooldown=None):
        if cooldown is None:
            cooldown = self.alert_audio_length
            
        now = time.time()
        last = self.last_event_called_time.get(event_name, 0)

        if now - last < cooldown:
            return False

        self.last_event_called_time[event_name] = now
        return True
    
    def is_any_known_person(self):
        '''Check nếu có ít nhất 1 người quen trong nhà.'''
        for det in self.objects.values():
            if det.type == "person" and not det.is_strange:
                return True
        return False

    def is_any_stranger(self):
        '''Check nếu có ít nhất 1 người lạ trong nhà.'''
        for det in self.objects.values():
            if det.type == "person" and det.is_strange:
                return True
        return False