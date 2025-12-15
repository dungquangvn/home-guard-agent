import cv2
import os
from datetime import datetime
from collections import deque

class VideoRecorder:
    """
    Simple video recorder for saving processed frames.
    Supports real-time camera or video file input.
    """

    def __init__(
        self,
        save_dir: str = "recordings",
        filename: str = None,
        fps: float = 30,
        width: int = None,
        height: int = None
    ):
        os.makedirs(save_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"record_{timestamp}.mp4"

        self.output_path = os.path.join(save_dir, filename)

        self.fps = fps
        self.width = width
        self.height = height

        self.writer = None

    def _init_writer(self):
        """Initialize the cv2.VideoWriter lazily (first frame)."""
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            self.output_path, fourcc, self.fps, (self.width, self.height)
        )
        print(f"[VideoRecorder] Started recording at: {self.output_path}")

    def write(self, frame):
        """
        Write a processed frame (already drawn with bounding boxes).
        """
        if frame is None:
            return

        if self.writer is None:
            h, w = frame.shape[:2]

            # auto-set width/height if user didn't specify
            if self.width is None:
                self.width = w
            if self.height is None:
                self.height = h

            self._init_writer()

        self.writer.write(frame)

    def release(self):
        if self.writer:
            print("[VideoRecorder] Saved video to:", self.output_path)
            self.writer.release()
            self.writer = None
            
class EventVideoRecorder:
    def __init__(self, height, width, fps, buffer_seconds=10):
        self.fps = fps
        self.width = width
        self.height = height
        self.max_frames = int(buffer_seconds * fps)
        print(f"[EventVideoRecorder] Initialized with buffer of {buffer_seconds}s ({self.max_frames} frames at {fps} FPS)")
        self.buffer = deque(maxlen=self.max_frames)

    def push(self, frame):
        self.buffer.append(frame.copy())

    def save_event(self, save_dir, filename):
        frames = list(self.buffer)
        
        recorder = VideoRecorder(
            save_dir=save_dir,
            filename=filename,
            fps=self.fps,
            width=self.width,
            height=self.height
        )
        for frame in frames:
            recorder.write(frame)
        recorder.release()
        fix_mp4_for_web(recorder.output_path)
        
import subprocess

def fix_mp4_for_web(path):
    tmp = path.replace(".mp4", "_web.mp4")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", path,
            "-map", "0:v:0",
            "-c:v", "libx264",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            tmp
        ],
        check=True
    )

    os.replace(tmp, path)
    
if __name__ == "__main__":
    fix_mp4_for_web("src/modules/server/front_end/react/public/event_1_20251215_221444.mp4")

