# src/modules/recognition/face_recognitor.py
from typing import List, Tuple
import cv2
import numpy as np
from ultralytics import YOLO
import asyncio
import time

class FaceRecognitor:
    def __init__(self, model_path='models/yolov12n-face.pt', conf=0.5):
        self.detector = YOLO(model_path)
        self.conf = conf
        print(f"Khởi tạo FaceRecognitor với mô hình {model_path}")

    async def track_faces(self, image: np.ndarray) -> List[Tuple[np.ndarray, int, float]]:
        results = self.detector.track(image, persist=True, conf=self.conf, verbose=False)
        
        r = results[0]
        
        face_data_list = []
        if r.boxes.id is None:
            return []  
            
        bbox_list = r.boxes.xyxy.cpu().numpy()           
        conf_score_list = r.boxes.conf.cpu().numpy()  
        track_id_list = r.boxes.id.cpu().numpy().astype(int)


        for bbox, conf, track_id in zip(bbox_list, conf_score_list, track_id_list):
            
            x1, y1, x2, y2 = map(int, bbox)
            face_img = image[y1:y2, x1:x2]
            
            face_data_list.append((face_img, track_id, conf))
            
        return face_data_list

async def main_test():
    print("--- Bắt đầu kiểm tra FaceRecognitor với video... ---")
    
    recognitor = FaceRecognitor(conf=0.5)
    
    video_path = "data/test_vid.mp4" 
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Lỗi: Không thể mở video tại {video_path}")
        return

    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kết thúc video.")
            break
            
        frame_count += 1
        
        if frame_count % 3 != 1:
            continue

        face_data_list = await recognitor.track_faces(frame)
        
        for (face_img, track_id, conf) in face_data_list:
            print(f"Frame {frame_count}: Phát hiện Face ID: {track_id} (Conf: {conf:.2f})")
            cv2.imshow(f"Face ID {track_id}", face_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    end_time = time.time()
    print(f"--- Kiểm tra hoàn tất ---")
    print(f"Tổng thời gian: {end_time - start_time:.2f}s")
    print(f"Đã xử lý {frame_count // 3} frames.")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
  
    asyncio.run(main_test())
