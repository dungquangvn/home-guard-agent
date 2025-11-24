from typing import List, Tuple, Optional
import cv2
import numpy as np

class Detection:
    def __init__(
        self, 
        bbox: Tuple[int, int, int, int],    # x, y, w, h
        # image: np.ndarray,
        # original_image: Optional[np.ndarray] = None,
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
        # self.image = image
        # self.original_image = original_image
        self.confidence = confidence
        self.is_strange = is_strange

    def set_is_strange(self, is_strange: bool):
        self.is_strange = is_strange


class Person(Detection):
    def __init__(self, bbox: Tuple[int, int, int, int], name: str = "Unknown", id: Optional[int] = None, is_strange: bool = False, confidence: float = 1.0):
        super().__init__(identity_id=id, type="person", confidence=confidence, bbox=bbox, is_strange=is_strange)
        self.name = name

    def __repr__(self):
        return f"Person(ID: {self.id}, Name: {self.name}, Strange: {self.is_strange})"


class Vehicle(Detection):
    def __init__(self, bbox: Tuple[int, int, int, int], vehicle_type: str = "car", plate_number: str = "Unknown", id: Optional[int] = None, is_strange: bool = False, confidence: float = 1.0):
        super().__init__(identity_id=id, type=vehicle_type, confidence=confidence, bbox=bbox, is_strange=is_strange)
        self.plate_number = plate_number

    def __repr__(self):
        return f"Vehicle(Type: {self.type}, Plate: {self.plate_number}, Is strange: {self.is_strange})"
    
class FrameData:
    def __init__(self, frame_id: int, image: np.ndarray):
        self.frame_id = frame_id        # ID của frame
        self.image = image              # Ảnh gốc (RGB hoặc BGR)
        self.objects: List[Detection] = []  # Các đối tượng detect/recognize
        
    def draw_object(self, detection: Detection):
        x, y, w, h = detection.bbox
        color = (0, 255, 0) if not detection.is_strange else (0, 0, 255)
        cv2.rectangle(self.image, (x, y), (x + w, y + h), color, 2)
        label = f"{detection.type} ({detection.confidence:.2f})"
        cv2.putText(self.image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
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
    
if __name__ == "__main__":
    image = cv2.imread("data/test_img.jpg", cv2.IMREAD_COLOR)
    image = cv2.resize(image, (640, 480))
    cv2.imshow("Test Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    frame = FrameData(frame_id=1, image=image)
    person = Person(id=101, bbox=(284, 128, 118, 270), is_strange=True)
    vehicle1 = Vehicle(vehicle_type="car", id=201, bbox=(275, 1, 134, 184), is_strange=False)
    vehicle2 = Vehicle(vehicle_type="car", id=202, bbox=(85, 12, 157, 188), is_strange=False)
    
    frame.add_object(person)
    frame.add_object(vehicle1)
    frame.add_object(vehicle2)
    
    cv2.imshow("Frame with Detections", frame.get_image())
    cv2.waitKey(0)
    cv2.destroyAllWindows()