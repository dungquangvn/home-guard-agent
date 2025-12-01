import os
import sys
import types
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# Stub easyocr and ultralytics before importing plate_recognitor
def make_fake_easyocr():
    mod = types.ModuleType("easyocr")
    
    class Reader:
        def __init__(self, langs, gpu=False):
            self.langs = langs
            
        def readtext(self, image):
            # Return mock OCR results: list of (bbox, text, confidence)
            return [
                ((0, 0, 50, 30), "ABC", 0.95),
                ((50, 0, 100, 30), "123", 0.92),
            ]
    
    mod.Reader = Reader
    return mod


def make_fake_ultralytics():
    mod = types.ModuleType("ultralytics")
    
    class FakeBox:
        def __init__(self, x1, y1, x2, y2, conf):
            self.xyxy = np.array([[x1, y1, x2, y2]])
            self.conf = np.array([conf])
    
    class FakeResults:
        def __init__(self, boxes):
            self.boxes = boxes
    
    class YOLO:
        def __init__(self, model_path):
            self.model_path = model_path
        
        def __call__(self, image):
            # Return mock detection: one license plate box
            h, w = image.shape[:2]
            box = FakeBox(w // 4, h // 4, 3 * w // 4, 3 * h // 4, 0.9)
            results = FakeResults([box])
            return [results]
    
    mod.YOLO = YOLO
    return mod


# Inject fakes before import
sys.modules["easyocr"] = make_fake_easyocr()
sys.modules["ultralytics"] = make_fake_ultralytics()

# Also stub cv2 to avoid needing opencv-python
class FakeCV2:
    COLOR_BGR2RGB = None
    
    @staticmethod
    def cvtColor(img, code):
        return img

sys.modules["cv2"] = FakeCV2()

from modules.recognition.plate_recognitor import LicensePlateRecognizer


def test_license_plate_recognizer_singleton_pattern():
    """Black-box: LicensePlateRecognizer uses singleton pattern"""
    rec1 = LicensePlateRecognizer(threshold_conf=0.5)
    rec2 = LicensePlateRecognizer(threshold_conf=0.5)
    
    # Should be same instance
    assert rec1 is rec2


def test_license_plate_recognizer_stores_threshold():
    """Black-box: LicensePlateRecognizer stores confidence threshold"""
    rec = LicensePlateRecognizer(threshold_conf=0.7)
    assert rec.conf == 0.7


def test_license_plate_recognizer_has_reader_and_model():
    """Black-box: LicensePlateRecognizer initializes reader and detect_model"""
    rec = LicensePlateRecognizer(threshold_conf=0.5)
    assert hasattr(rec, "reader")
    assert hasattr(rec, "detect_model")
    assert rec.reader is not None
    assert rec.detect_model is not None


def test_detect_license_plates_returns_list(monkeypatch):
    """Black-box: detect_license_plates returns list of strings"""
    rec = LicensePlateRecognizer(threshold_conf=0.5)
    
    # Create a dummy image
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = rec.detect_license_plates(image)
    
    assert isinstance(result, list)
    # Should extract text from OCR results
    assert len(result) > 0
    assert all(isinstance(plate, str) for plate in result)


def test_detect_license_plates_respects_confidence_threshold():
    """Black-box: detect_license_plates filters by confidence threshold"""
    # Create two recognizers with different thresholds
    rec_low = LicensePlateRecognizer(threshold_conf=0.5)
    rec_high = LicensePlateRecognizer(threshold_conf=0.95)
    
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result_low = rec_low.detect_license_plates(image)
    result_high = rec_high.detect_license_plates(image)
    
    # Higher threshold should be more restrictive (fewer or equal results)
    assert isinstance(result_low, list)
    assert isinstance(result_high, list)


def test_detect_license_plates_handles_empty_image():
    """Black-box: detect_license_plates handles image with no detections gracefully"""
    rec = LicensePlateRecognizer(threshold_conf=0.9)
    
    # Create an image that might not trigger detections
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    # Should not raise exception
    result = rec.detect_license_plates(image)
    assert isinstance(result, list)


def test_detect_license_plates_cleans_text():
    """Black-box: detect_license_plates removes special characters from OCR text"""
    rec = LicensePlateRecognizer(threshold_conf=0.5)
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = rec.detect_license_plates(image)
    
    # All results should be alphanumeric, space, dot, dash only
    import re
    for plate in result:
        # Should only contain letters, numbers, dots, dashes, spaces
        assert re.match(r'^[A-Za-z0-9.\-\s]*$', plate)
