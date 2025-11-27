from src.modules.recognition.face_recognitor import FaceRecognitor
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger

def on_new_person(face_recognitor: FaceRecognitor, logger: Logger, state_manager: StateManager):
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
        
        logger.info(f"Phát hiện người mới tại ({x}, {y}), cố gắng nhận diện...")
        
        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        person_image = frame_image[y1:y2, x1:x2, :]


        # Cố gắng nhận diện
        people = face_recognitor.recognize_faces([person_image])
        identity_id = people[0]['identity_id']
        name = people[0]['name']
        score = people[0]['score']
        
        detection.identity_id = identity_id
        detection.type = "person"
        detection.name = name
        detection.confidence = score
        detection.is_strange = (name == "Unknown")
        
        detection.is_recognized = True
        detection.is_processing = False

        # Xử lý dựa vào kết quả nhận diện
        if detection.is_strange:
            logger.info(
                f"[Person {detection.tracker_id}] Người lạ xuất hiện (không nhận diện được)"
            )
        else:
            logger.info(
                f"[Person {detection.tracker_id}] Người quen: {identity_id} (score={score:.2f})"
            )
            
        state_manager.update(detection)

    return handler