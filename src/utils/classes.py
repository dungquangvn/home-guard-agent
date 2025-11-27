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
        self.is_processing = True

        # Nếu type là person
        self.name = "unknown"
        
        # Nếu type in ['car', 'motorcycle']
        self.plate_number = "unknown"
    
class FrameData:
    def __init__(self, frame_id: int, image: np.ndarray):
        self.frame_id = frame_id        # ID của frame
        self.image = image              # Ảnh gốc (RGB hoặc BGR)
        self.objects: List[Detection] = []  # Các đối tượng detect/recognize
        
    def draw_object(self, detection: Detection):
        if detection.is_processing:
            color = (0, 255, 255)   # Yellow: pending recognize

        elif detection.is_strange:
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
            if detection.is_processing:
                label = f"human | pending"
            elif detection.is_recognized:
                label = f"human | name: {detection.name} | id: {detection.identity_id} | {detection.confidence:.2f}"
            else:
                label = f"human | name: unknown"
        elif detection.type == 'motorcycle':
            if detection.is_processing:
                label = f"motorcycle | pending"
            elif detection.is_recognized:
                label = f"motorcycle | plate number: {detection.plate_number} | {detection.confidence:.2f}"
            else:
                label = f"motorcycle | plate number: unknown"
        elif detection.type == 'car':
            if detection.is_processing:
                label = f"car | pending"
            elif detection.is_recognized:
                label = f"car | plate number: {detection.plate_number} | {detection.confidence:.2f}"
            else:
                label = f"car | plate number: unknown"
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