from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.alerts.alert_service import AlertService
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import os, cv2, datetime

RECOGNITION_TIMEOUT = 5.0

executor = ThreadPoolExecutor(max_workers=3)

def on_new_person(face_recognitor: FaceRecognitor, alert_service: AlertService, logger: Logger, state_manager: StateManager):
    """
    Handler cho event "new_person".
    Event format:
    {
        "event": "new_person",
        "data": Detection,
        "frame": FrameData
    }
    """

    def handler(event):
        detection = event["data"]
        frame_image = event["frame"].get_image()
        bbox = detection.bbox
        x, y, w, h = bbox
        
        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        person_image = frame_image[y1:y2, x1:x2, :]

        future = executor.submit(
            face_recognitor.recognize_faces,
            [person_image]
        )

        # Cố gắng nhận diện
        try:
            people = future.result(timeout=RECOGNITION_TIMEOUT)
            identity_id = people[0]['identity_id']
            name = people[0]['name']
            score = people[0]['score']
            
        except TimeoutError:
            # HẾT 5s → BỎ LUÔN
            future.cancel()
            identity_id = None
            name = "Unknown"
            score = 0.0

            logger.info(
                title="[RECOGNITION] Nhận diện khuôn mặt bị timeout",
                message=f"Quá thời gian chờ {RECOGNITION_TIMEOUT}s cho Track, đánh dấu là người lạ. (Track ID={detection.tracker_id})"
            )
        
        detection.identity_id = identity_id
        detection.type = "person"
        detection.name = name
        detection.confidence = score
        detection.is_strange = (name == "Unknown")
        
        detection.is_recognized = True
        detection.is_processing = False

        frame_image_path = f'src/modules/server/front_end/react/public/frame_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        frame_image_name = os.path.basename(frame_image_path)
        os.makedirs('src/modules/server/front_end/react/public/', exist_ok=True)
        cv2.imwrite(frame_image_path, person_image)
        
        # Xử lý dựa vào kết quả nhận diện
        if not detection.is_strange:
            alert_service.stop_alarm_sound()
            logger.info(
                title="[EVENT] Người quen xuất hiện",
                message=f"{detection.name} (ID={detection.identity_id})",
                file_path=frame_image_name
            )
        else:
            logger.info(
                title="[EVENT] Người lạ xuất hiện",
                message=f"Người lạ (ID={detection.tracker_id})",
                file_path=frame_image_name
            )
            
        state_manager.update(detection)

    return handler