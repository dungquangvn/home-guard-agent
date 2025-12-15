from src.modules.recognition.plate_recognitor import CustomLicensePlateRecognizer
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
import pprint
import os, cv2, datetime

ID_PLATE_NUMBER_MAP = {
    '201': '19s2-45678',
    '202': '19s1-37994',
    '203': '4fyy456'
}

PLATE_NUMBER_ID_MAP = {v: k for k, v in ID_PLATE_NUMBER_MAP.items()}

def on_new_vehicle(plate_recognitor: CustomLicensePlateRecognizer, logger: Logger, state_manager: StateManager):
    """
    Handler cho event "new_vehicle".
    Event format:
    {
        "event": "new_vehicle",
        "data": Detection,
        "frame": FrameData
    }
    """
    def handler(event):
        detection = event["data"]          # Detection object
        if detection.type == "bicycle":
            # Bỏ qua xe đạp
            logger.info(f"[EVENT] Phát hiện xe đạp mới.")
            detection.identity_id = None
            detection.plate_number = "N/A"
            detection.is_strange = False
            detection.is_recognized = True
            detection.is_processing = False

            state_manager.update(detection)
            return
        
        frame_image = event["frame"].get_image()
        bbox = detection.bbox
        x, y, w, h = bbox
        
        # --- Crop vùng xe ---
        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        vehicle_crop = frame_image[y1:y2, x1:x2, :]

        # --- Nhận diện biển số ---
        plates = plate_recognitor.detect_license_plates(vehicle_crop)

        frame_image_path = f'src/modules/server/front_end/react/public/frame_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        frame_image_name = os.path.basename(frame_image_path)
        os.makedirs('src/modules/server/front_end/react/public/', exist_ok=True)
        cv2.imwrite(frame_image_path, vehicle_crop)

        if len(plates) == 0:
            # Không đọc được hoặc không tìm thấy biển số
            logger.info(
                title="[EVENT] Xe lạ – không nhận diện được biển số",
                message=f"Không tìm thấy biển số trên xe (Track ID={detection.tracker_id})",
                file_path=frame_image_name
            )
            
            detection.identity_id = None
            detection.plate_number = "Unknown"
            detection.is_strange = True
            detection.is_recognized = False
            detection.is_processing = True

            state_manager.update(detection)
            return

        plate_number = plates[0]
        identity_id = PLATE_NUMBER_ID_MAP.get(plate_number, None)
        score = 0.5

        # --- Gán kết quả vào detection ---
        detection.identity_id = identity_id
        detection.plate_number = plate_number
        detection.confidence = score
        detection.type = detection.type  # giữ nguyên car/motorcycle/bicycle
        detection.is_strange = (identity_id == None or plate_number == "Unknown")

        detection.is_recognized = True
        detection.is_processing = False

        # --- Logging theo kết quả ---
        if detection.is_strange:
            logger.info(
                title="[EVENT] Xe lạ xuất hiện",
                message=f"Xe lạ với biển số {plate_number} (Track ID={detection.tracker_id})"
            )
        else:
            logger.info(
                title="[EVENT] Xe quen xuất hiện",
                message=f"Xe với biển số {plate_number} (ID={identity_id})"
            )

        # --- Cập nhật state ---
        state_manager.update(detection)

    return handler
