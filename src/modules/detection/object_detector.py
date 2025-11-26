from typing import List, Tuple
import numpy as np
import cv2
from ultralytics import YOLO
import asyncio
import os

class PersonDetector:
    PERSON_CLASS_ID = 0

    def __init__(self, model_path: str = 'models/yolo11n.pt', conf_threshold: float = 0.5):
        self.model = YOLO(model_path, verbose=False)
        self.conf_threshold = conf_threshold
    
    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        results = self.model(frame)[0]

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if cls_id == self.PERSON_CLASS_ID and conf >= self.conf_threshold:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append((int(x1), int(y1), int(x2), int(y2), conf))
        return detections
    

    def crop_persons(self, frame: np.ndarray, detections: List[Tuple[int,int,int,int,float]]) -> List[np.ndarray]:
        """
        Trả về list các ảnh đã cắt ra từ bounding box của người
        """
        crops = []
        h, w = frame.shape[:2]
        for (x1, y1, x2, y2, conf) in detections:
            # đảm bảo không vượt biên
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            crop = frame[y1:y2, x1:x2].copy()
            crops.append(crop)
        return crops

if __name__ == "__main__":
    detector = PersonDetector("models/yolo11n.pt", conf_threshold=0.5)
    
    frame = cv2.imread("data/test_img.jpg")
    persons = detector.detect(frame)

    crops = detector.crop_persons(frame, persons)

    # Lưu từng người ra file hoặc hiển thị
    for i, crop in enumerate(crops):
        cv2.imshow(f"Person {i}", crop)
        cv2.imwrite(f"person_{i}.jpg", crop)
    cv2.waitKey(0)
    cv2.destroyAllWindows()