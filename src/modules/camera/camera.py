import cv2
from src.utils.classes import FrameData


class Camera:
    def __init__(self, source=0):
        """
        source:
            0 -> laptop webcam
            'video.mp4' -> video file
        """
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open camera/video source: {source}")

        self.source = source
        self.frame_id = 0

        source_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = source_fps if source_fps and source_fps > 1e-3 else 30.0

        # Most file-based sources expose frame count > 0, live sources usually do not.
        self.is_file_source = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0
        if not self.is_file_source:
            # Keep only a very small capture buffer to reduce live latency.
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Camera] Opened source: {source} (FPS={self.fps}, W={self.width}, H={self.height})")

    def get_frame(self):
        """Read one frame and return FrameData."""
        ret, frame = self.cap.read()
        if not ret:
            return None

        self.frame_id += 1
        return FrameData(frame_id=self.frame_id, image=frame)

    def drop_frames(self, count: int) -> int:
        """Drop old frames and return how many were dropped."""
        if count <= 0:
            return 0

        dropped = 0
        for _ in range(count):
            if not self.cap.grab():
                break
            self.frame_id += 1
            dropped += 1
        return dropped

    def release(self):
        """Release camera/video resources."""
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    cam = Camera(source="data/test_vid.mp4")  # 0 = laptop webcam
    while True:
        frame_data = cam.get_frame()
        if frame_data is None:
            break

        cv2.imshow("Camera", frame_data.image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
