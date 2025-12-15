from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.alerts.alert_service import AlertService
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from concurrent.futures import ThreadPoolExecutor, TimeoutError

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
                f"[TIMEOUT] Không nhận diện được sau {RECOGNITION_TIMEOUT}s. ID={detection.tracker_id}"
            )
        
        detection.identity_id = identity_id
        detection.type = "person"
        detection.name = name
        detection.confidence = score
        detection.is_strange = (name == "Unknown")
        
        detection.is_recognized = True
        detection.is_processing = False

        # Xử lý dựa vào kết quả nhận diện
        if not detection.is_strange:
            alert_service.stop_alarm_sound()
            logger.info(
                f"[EVENT] {detection.name} xuất hiện. ID={identity_id}, score={score:.2f})"
            )
        else:
            logger.info(
                f"[EVENT] Người lạ xuất hiện. ID={detection.tracker_id}"
            )
            
        state_manager.update(detection)

    return handler