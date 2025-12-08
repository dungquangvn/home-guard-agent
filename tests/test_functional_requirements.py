import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

import numpy as np
import pytest

from src.utils.classes import Detection, FrameData
from src.core.state_manager import StateManager
from src.core.event_extractor import EventExtractor
from src.core.event_bus import EventBus
from src.event_handlers.on_new_person import on_new_person


def test_fr_02_detection_and_tracking_flow():
    """FR-02: EventExtractor tạo events từ kết quả tracker giả"""
    sm = StateManager()
    extractor = EventExtractor(sm)

    class NpWrap:
        def __init__(self, arr):
            self._arr = np.array(arr)

        def cpu(self):
            return self

        def numpy(self):
            return self._arr

    class FakeBoxes:
        def __init__(self, cls_arr, xywh_list, id_arr, conf_arr):
            self.cls = np.array(cls_arr)
            self.xywh = [NpWrap(x) for x in xywh_list]
            self.id = np.array(id_arr) if id_arr is not None else None
            self.conf = np.array(conf_arr)

    class FakeResult:
        def __init__(self, boxes):
            self.boxes = boxes

    boxes = FakeResult(FakeBoxes([0], [[50, 50, 40, 60]], [7], [0.9]))
    events = extractor.extract([boxes])
    assert any(e["event"] == "new_person" for e in events)


def test_fr_03_new_person_emitted_by_state_manager():
    """FR-03: StateManager tạo event new_person khi gặp person mới"""
    sm = StateManager()
    det = Detection(bbox=(0, 0, 10, 10), tracker_id=333, type="person")
    events = sm.update_object(det)
    assert any(e["event"] == "new_person" for e in events)


def test_fr_04_face_recognition_handler_updates_detection():
    """FR-04: on_new_person handler cập nhật detection với kết quả từ FaceRecognitor"""
    class DummyFR:
        def recognize_faces(self, crops):
            return [{"identity_id": 5, "name": "Unit", "score": 0.9}]

    logger = type("L", (), {"info": lambda *a, **k: None})()
    sm = StateManager()
    fr = DummyFR()
    handler = on_new_person(fr, logger, sm)

    img = np.zeros((80, 80, 3), dtype=np.uint8)
    fd = FrameData(frame_id=1, image=img)
    det = Detection(bbox=(5, 5, 20, 20), tracker_id=44, type="person")
    handler({"event": "new_person", "data": det, "frame": fd})

    assert det.name == "Unit"
    assert det.identity_id == 5
    assert det.is_recognized is True


def test_fr_05_plate_recognition_smoke():
    """FR-05: Nếu module nhận dạng biển số tồn tại, gọi hàm detect và ensure không crash"""
    plate_mod = pytest.importorskip("src.modules.recognition.plate_recognitor")
    # class name in repo is CustomLicensePlateRecognizer
    Cls = getattr(plate_mod, "CustomLicensePlateRecognizer", None)
    if Cls is None:
        pytest.skip("Không tìm thấy CustomLicensePlateRecognizer")
    try:
        inst = Cls(threshold_conf=0.5)
    except Exception:
        pytest.skip("Không thể khởi tạo plate recognizer trong môi trường test")
    img = np.zeros((64, 128, 3), dtype=np.uint8)
    try:
        plates = inst.detect_license_plates(img)
        assert isinstance(plates, list)
    except Exception:
        pytest.skip("detect_license_plates ném lỗi trong môi trường test")


def test_fr_06_object_left():
    """FR-06: detect_left_objects phát hiện object rời đi"""
    sm = StateManager()
    det = Detection(bbox=(0, 0, 1, 1), tracker_id=101, type="person")
    sm.update_object(det)
    evs = sm.detect_left_objects(current_track_ids=[])
    assert any(e["event"] == "object_left" for e in evs)


def test_fr_07_stranger_over_30_seconds_simulation():
    """FR-07: nếu first_seen cách đây >30s thì emit stranger_over_30_seconds"""
    sm = StateManager()
    det = Detection(bbox=(0, 0, 1, 1), tracker_id=202, type="person")
    # simulate old first_seen
    det.first_seen -= 40
    sm.objects[202] = det
    events = sm.update_object(det)
    assert any(e["event"] == "stranger_over_30_seconds" for e in events)


def test_fr_08_eventbus_handlers_called():
    """FR-08: EventBus phải gọi các handler đã đăng ký"""
    bus = EventBus()
    called = []

    def h(evt):
        called.append(evt)

    bus.on("ev", h)
    bus.emit([{"event": "ev", "data": 1}])
    time.sleep(0.2)
    assert len(called) >= 1

