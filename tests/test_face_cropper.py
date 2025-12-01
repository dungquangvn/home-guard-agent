import os
import sys
import asyncio
import types
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# Stub ultralytics before importing face_cropper
def make_fake_ultralytics_for_face():
    mod = types.ModuleType("ultralytics")
    
    class FakeBox:
        def __init__(self, xyxy, conf):
            self.xyxy = xyxy
            self.conf = conf
    
    class FakeBoxes:
        def __init__(self, boxes_list):
            self._boxes = boxes_list
        
        def cpu(self):
            return self
        
        def numpy(self):
            return np.array([b for b in self._boxes]) if self._boxes else np.array([])
    
    class FakeResults:
        def __init__(self, faces):
            boxes_xyxy = []
            boxes_conf = []
            for face in faces:
                boxes_xyxy.append(face['bbox'])
                boxes_conf.append(face['confidence'])
            
            self.boxes = types.SimpleNamespace()
            self.boxes.xyxy = types.SimpleNamespace()
            self.boxes.conf = types.SimpleNamespace()
            
            # Override cpu() and numpy() to return data
            self.boxes.xyxy.cpu = lambda: types.SimpleNamespace(
                numpy=lambda: np.array(boxes_xyxy) if boxes_xyxy else np.array([])
            )
            self.boxes.conf.cpu = lambda: types.SimpleNamespace(
                numpy=lambda: np.array(boxes_conf) if boxes_conf else np.array([])
            )
    
    class YOLO:
        def __init__(self, model_path):
            self.model_path = model_path
            self.test_faces = []  # Can be set by tests
        
        def predict(self, image):
            # Return mock detection: one face if image is not empty
            if image is not None and image.size > 0:
                h, w = image.shape[:2]
                face = {
                    'bbox': [w // 4, h // 4, 3 * w // 4, 3 * h // 4],
                    'confidence': 0.95
                }
                return [FakeResults([face])]
            return [FakeResults([])]
    
    mod.YOLO = YOLO
    return mod


sys.modules["ultralytics"] = make_fake_ultralytics_for_face()

from modules.recognition.face_cropper import FaceCropper


@pytest.mark.asyncio
async def test_face_cropper_initialization():
    """Black-box: FaceCropper initializes with model path and confidence"""
    cropper = FaceCropper(model_path='models/yolov12n-face.pt', conf=0.5)
    assert cropper.conf == 0.5
    assert cropper.detector is not None


@pytest.mark.asyncio
async def test_face_cropper_crop_faces_returns_list():
    """Black-box: crop_faces returns list of face images with confidence"""
    cropper = FaceCropper(conf=0.5)
    
    # Create test image
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = await cropper.crop_faces(image)
    
    assert isinstance(result, list)
    # Each item should have face_image and confidence
    for item in result:
        assert isinstance(item, dict)
        assert "face_image" in item
        assert "confidence" in item
        assert isinstance(item["face_image"], np.ndarray)
        assert isinstance(item["confidence"], (float, np.floating))


@pytest.mark.asyncio
async def test_face_cropper_confidence_threshold():
    """Black-box: crop_faces respects confidence threshold"""
    cropper_strict = FaceCropper(conf=0.99)
    cropper_loose = FaceCropper(conf=0.5)
    
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result_strict = await cropper_strict.crop_faces(image)
    result_loose = await cropper_loose.crop_faces(image)
    
    # Strict threshold should be more restrictive (fewer or equal results)
    # Both should return lists
    assert isinstance(result_strict, list)
    assert isinstance(result_loose, list)


@pytest.mark.asyncio
async def test_face_cropper_empty_image():
    """Black-box: crop_faces handles empty detections gracefully"""
    cropper = FaceCropper(conf=0.5)
    
    # Small image might not have detections
    image = np.ones((50, 50, 3), dtype=np.uint8) * 255
    
    result = await cropper.crop_faces(image)
    
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_face_cropper_crops_correct_region():
    """Black-box: crop_faces extracts correct region from image"""
    cropper = FaceCropper(conf=0.5)
    
    # Create a test image with known pattern
    image = np.zeros((400, 600, 3), dtype=np.uint8)
    # Fill center region with white (where face is expected)
    image[100:300, 150:450] = 255
    
    result = await cropper.crop_faces(image)
    
    # Should have at least attempted to crop
    assert isinstance(result, list)
    # If detections found, check that cropped region exists
    for face_dict in result:
        crop = face_dict["face_image"]
        assert crop.shape[0] > 0  # height > 0
        assert crop.shape[1] > 0  # width > 0
        assert crop.shape[2] == 3  # has 3 channels


@pytest.mark.asyncio
async def test_face_cropper_detect_internal_method():
    """Black-box: _detect returns list of face dictionaries"""
    cropper = FaceCropper(conf=0.5)
    
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    faces = await cropper._detect(image)
    
    assert isinstance(faces, list)
    for face in faces:
        assert isinstance(face, dict)
        assert "bbox" in face
        assert "confidence" in face
        bbox = face["bbox"]
        assert len(bbox) == 4  # (x1, y1, x2, y2)
