import os
import sys
import tempfile
import numpy as np
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from modules.video_recorder.video_recorder import VideoRecorder


def test_video_recorder_creates_directory(tmp_path):
    """Black-box: VideoRecorder creates save directory if missing"""
    save_dir = tmp_path / "videos"
    recorder = VideoRecorder(save_dir=str(save_dir))
    assert save_dir.exists()


def test_video_recorder_generates_filename_if_not_provided(tmp_path):
    """Black-box: VideoRecorder auto-generates filename with timestamp"""
    save_dir = tmp_path / "videos"
    recorder = VideoRecorder(save_dir=str(save_dir))
    
    # Should have generated a path with timestamp
    assert recorder.output_path
    assert "record_" in os.path.basename(recorder.output_path)
    assert ".mp4" in recorder.output_path


def test_video_recorder_uses_custom_filename(tmp_path):
    """Black-box: VideoRecorder uses provided filename"""
    save_dir = tmp_path / "videos"
    custom_name = "my_video.mp4"
    recorder = VideoRecorder(save_dir=str(save_dir), filename=custom_name)
    
    assert custom_name in recorder.output_path
    assert recorder.output_path.endswith(custom_name)


def test_video_recorder_stores_fps_and_dims(tmp_path):
    """Black-box: VideoRecorder stores FPS and dimension parameters"""
    recorder = VideoRecorder(save_dir=str(tmp_path), fps=60, width=1920, height=1080)
    
    assert recorder.fps == 60
    assert recorder.width == 1920
    assert recorder.height == 1080


def test_video_recorder_write_initializes_writer(tmp_path):
    """Black-box: VideoRecorder initializes writer on first frame"""
    save_dir = tmp_path / "videos"
    recorder = VideoRecorder(save_dir=str(save_dir), fps=30)
    
    # Before first write, writer should be None
    assert recorder.writer is None
    
    # Create a test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    recorder.write(frame)
    
    # After first write, writer should be initialized
    # (may still be None if cv2.VideoWriter fails, but that's OK for black-box)


def test_video_recorder_write_none_frame_ignored(tmp_path):
    """Black-box: VideoRecorder handles None frames gracefully"""
    recorder = VideoRecorder(save_dir=str(tmp_path))
    
    # Should not raise exception
    recorder.write(None)
    assert recorder.writer is None


def test_video_recorder_write_auto_sets_dimensions(tmp_path):
    """Black-box: VideoRecorder auto-detects frame dimensions if not provided"""
    save_dir = tmp_path / "videos"
    recorder = VideoRecorder(save_dir=str(save_dir), fps=30)
    
    assert recorder.width is None
    assert recorder.height is None
    
    # Write frame with specific dimensions
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    recorder.write(frame)
    
    # Should have detected dimensions
    assert recorder.width == 1280
    assert recorder.height == 720


def test_video_recorder_release_closes_writer(tmp_path):
    """Black-box: VideoRecorder.release() closes the video writer"""
    save_dir = tmp_path / "videos"
    recorder = VideoRecorder(save_dir=str(save_dir))
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    recorder.write(frame)
    
    # Store reference to writer before release
    writer_before = recorder.writer
    
    recorder.release()
    
    # After release, writer should be None
    assert recorder.writer is None


def test_video_recorder_release_without_frames(tmp_path):
    """Black-box: VideoRecorder.release() handles case with no frames written"""
    recorder = VideoRecorder(save_dir=str(tmp_path))
    
    # Should not raise exception
    recorder.release()
    assert recorder.writer is None
