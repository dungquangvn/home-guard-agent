import os
import sys
import pytest
import asyncio
import tempfile
import cv2
import numpy as np
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Inject fake classes into sys.modules BEFORE importing utils.classes
class FakeFrameData:
    def __init__(self, frame_id, image):
        self.frame_id = frame_id
        self.image = image

sys.modules['utils.classes'] = MagicMock(FrameData=FakeFrameData)

from modules.camera.camera import Camera


class FakeCapture:
    """Fake cv2.VideoCapture for testing"""
    def __init__(self, source, opens=True, fps=30, width=640, height=480):
        self.source = source
        self._opens = opens
        self._fps = fps
        self._width = width
        self._height = height
        self._released = False
        self._frame_count = 0
        self._max_frames = 10

    def isOpened(self):
        return self._opens and not self._released

    def get(self, prop_id):
        if prop_id == cv2.CAP_PROP_FPS:
            return self._fps
        elif prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return self._width
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return self._height
        return 0

    def read(self):
        if not self.isOpened() or self._frame_count >= self._max_frames:
            return False, None
        
        self._frame_count += 1
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        frame[:, :] = [100, 100, 100]  # Gray frame
        return True, frame

    def release(self):
        self._released = True


class TestCamera:
    """Black-box tests for Camera class"""
    
    def test_camera_init_success(self, monkeypatch):
        """Black-box: Camera initializes successfully with valid source"""
        fake_cap = FakeCapture(source=0)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        assert cam.frame_id == 0
        assert cam.fps == 30
        assert cam.width == 640
        assert cam.height == 480
    
    
    def test_camera_init_with_video_file(self, monkeypatch):
        """Black-box: Camera initializes with video file path"""
        fake_cap = FakeCapture(source="video.mp4")
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source="video.mp4")
        
        assert cam.frame_id == 0
    
    
    def test_camera_init_raises_on_invalid_source(self, monkeypatch):
        """Black-box: Camera raises ValueError when source cannot be opened"""
        fake_cap = FakeCapture(source="invalid", opens=False)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        with pytest.raises(ValueError):
            Camera(source="invalid")
    
    
    def test_camera_get_frame_success(self, monkeypatch):
        """Black-box: get_frame returns FrameData with incremented frame_id"""
        fake_cap = FakeCapture(source=0)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        frame_data = cam.get_frame()
        
        assert frame_data is not None
        assert frame_data.frame_id == 1
        assert frame_data.image is not None
        assert isinstance(frame_data.image, np.ndarray)
    
    
    def test_camera_get_frame_increments_id(self, monkeypatch):
        """Black-box: get_frame increments frame_id on each call"""
        fake_cap = FakeCapture(source=0)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        frame1 = cam.get_frame()
        frame2 = cam.get_frame()
        frame3 = cam.get_frame()
        
        assert frame1.frame_id == 1
        assert frame2.frame_id == 2
        assert frame3.frame_id == 3
    
    
    def test_camera_get_frame_returns_none_on_end(self, monkeypatch):
        """Black-box: get_frame returns None when no more frames available"""
        fake_cap = FakeCapture(source=0, width=640, height=480)
        fake_cap._max_frames = 2  # Only 2 frames available
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        cam.get_frame()  # frame 1
        cam.get_frame()  # frame 2
        frame3 = cam.get_frame()  # no more frames
        
        assert frame3 is None
    
    
    def test_camera_get_frame_returns_none_on_read_failure(self, monkeypatch):
        """Black-box: get_frame returns None when cap.read() fails"""
        fake_cap = FakeCapture(source=0)
        fake_cap._opens = False
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        # Manually set cap to closed
        cam.cap = fake_cap
        
        frame_data = cam.get_frame()
        
        assert frame_data is None
    
    
    def test_camera_release_calls_destroy_windows(self, monkeypatch):
        """Black-box: release() calls cv2.destroyAllWindows()"""
        fake_cap = FakeCapture(source=0)
        destroy_mock = MagicMock()
        
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        monkeypatch.setattr("modules.camera.camera.cv2.destroyAllWindows", destroy_mock)
        
        cam = Camera(source=0)
        cam.release()
        
        assert fake_cap._released
        destroy_mock.assert_called_once()
    
    
    def test_camera_fps_property(self, monkeypatch):
        """Black-box: Camera stores FPS from video capture"""
        fake_cap = FakeCapture(source=0, fps=24)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        assert cam.fps == 24
    
    
    def test_camera_frame_dimensions(self, monkeypatch):
        """Black-box: Camera stores frame width and height"""
        fake_cap = FakeCapture(source=0, width=1280, height=720)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        assert cam.width == 1280
        assert cam.height == 720
    
    
    def test_camera_multiple_frames(self, monkeypatch):
        """Black-box: Camera can read multiple sequential frames"""
        fake_cap = FakeCapture(source=0)
        monkeypatch.setattr("modules.camera.camera.cv2.VideoCapture", lambda src: fake_cap)
        
        cam = Camera(source=0)
        
        frames = []
        for _ in range(5):
            frame = cam.get_frame()
            if frame is None:
                break
            frames.append(frame)
        
        assert len(frames) == 5
        # Check IDs are sequential
        for i, frame in enumerate(frames, 1):
            assert frame.frame_id == i
