from typing import List, Tuple, Optional
import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

class Detection:
    def __init__(
        self, 
        bbox: Tuple[float, float, float, float],    # x, y, w, h
        tracker_id: int | None = -1,                    # Là id tracker gán
        identity_id: int | None = -1,                   # Là id trong database, recognitor gán
        type: str = "unknown", 
        confidence: float = 0.5,
        is_strange: bool = False
    ):
        self.tracker_id = tracker_id
        self.identity_id = identity_id
        self.type = type
        self.bbox = bbox
        self.confidence = confidence
        self.is_strange = is_strange
        
        self.first_seen = time.time()
        self.last_seen = self.first_seen
        self.is_recognized = False      # đã hoàn thành nhận diện hay chưa
        self.last_recognized_time = -1
        self.recognition_attempts = 0
        self.is_processing = True
        self.recognition_history = []         # [{identity_id, name, score}, ...]
        self.last_logged_identity_key = None  # tuple(identity_id_or_-1, normalized_name)
        self.stable_identity_key = None       # tuple(identity_id_or_-1, normalized_name)
        self.recognition_state = "pending"    # pending|collecting|stable_known|stable_unknown|corrected

        # Nếu type là person
        self.name = "unknown"
        
        # Nếu type in ['car', 'motorcycle', 'bicycle']
        self.plate_number = "unknown"
    
class FrameData:
    def __init__(self, frame_id: int, image: np.ndarray):
        self.frame_id = frame_id        # ID của frame
        self.image = image              # Ảnh gốc (RGB hoặc BGR)
        self.objects: List[Detection] = []  # Các đối tượng detect/recognize
        
    def draw_object(self, detection: Detection):
        if detection.type in ["person", "car", "motorcycle"] and detection.recognition_state in ["pending", "collecting"]:
            color = (0, 255, 255)   # Yellow: pending recognize
        elif detection.type in ["person", "car", "motorcycle"] and detection.recognition_state == "corrected":
            color = (0, 165, 255)   # Orange: corrected
        elif detection.type in ["person", "car", "motorcycle"] and detection.recognition_state == "stable_unknown":
            color = (0, 0, 255)     # Red: stranger
        else:
            color = (0, 255, 0)  # Green: normal

        x, y, w, h = detection.bbox
        h_img, w_img = self.image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(w_img - 1, int(x + w))
        y2 = min(h_img - 1, int(y + h))
        cv2.rectangle(self.image, (x1, y1), (x2, y2), color, 2)

        if detection.type == 'person':
            if detection.recognition_state == "pending":
                label = f"human | pending"
            elif detection.recognition_state == "collecting":
                votes = len(detection.recognition_history)
                label = f"human | collected {votes} faces..."
            elif detection.recognition_state in ["stable_known", "corrected"]:
                label = f"human | name: {detection.name} | id: {detection.identity_id} | {detection.confidence:.2f}"
            elif detection.recognition_state == "stable_unknown":
                label = f"human | name: unknown | {detection.confidence:.2f}"
            else:
                label = f"human | name: unknown"
        elif detection.type in ['motorcycle', 'car']:
            vehicle_type = detection.type
            if detection.recognition_state == "pending":
                label = f"{vehicle_type} | pending"
            elif detection.recognition_state == "collecting":
                votes = len(detection.recognition_history)
                label = f"{vehicle_type} | collected {votes} plates..."
            elif detection.recognition_state in ["stable_known", "corrected"]:
                label = (
                    f"{vehicle_type} | plate number: {detection.plate_number} "
                    f"| id: {detection.identity_id} | {detection.confidence:.2f}"
                )
            elif detection.recognition_state == "stable_unknown":
                label = f"{vehicle_type} | plate number: unknown | {detection.confidence:.2f}"
            else:
                label = f"{vehicle_type} | plate number: unknown"
        elif detection.type == 'bicycle':
            label = f"bicycle"

        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(self.image, (x1, y1 - text_h - 6), (x1 + text_w + 4, y1), color, -1)
        cv2.putText(self.image, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        
    def add_object(self, detection: Detection):
        self.objects.append(detection)
        self.draw_object(detection)
    
    def get_objects(self) -> List[Detection]:
        return self.objects
    
    def clear_objects(self):
        self.objects = []
        
    def get_image(self) -> np.ndarray:
        return self.image
    
    def get_id(self):
        return self.frame_id
