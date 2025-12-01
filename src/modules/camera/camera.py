import cv2
import numpy as np
from utils.classes import FrameData

class Camera:
    def __init__(self, source=0):
        """
        source: 
            0 -> camera laptop
            'video.mp4' -> file video test
        """
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError(f"Không thể mở camera/video từ nguồn: {source}")
        self.frame_id = 0

    def get_frame(self):
        """Đọc 1 frame từ camera và trả về FrameData"""
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        self.frame_id += 1
        return FrameData(frame_id=self.frame_id, image=frame)

    def release(self):
        """Giải phóng camera"""
        self.cap.release()
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    cam = Camera(source="data/test_vid.mp4")  # 0 = webcam laptop
    while True:
        frame_data = cam.get_frame()
        if frame_data is None:
            break
        
        cv2.imshow("Camera", frame_data.image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()