from src.modules.recognition.plate_recognitor import CustomLicensePlateRecognizer
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
import os
import cv2
import datetime

ID_PLATE_NUMBER_MAP = {
    "201": "19s2-45678",
    "202": "19s1-37994",
    "203": "BOK5E1",
    "204": "B0K5E1",
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
        detection = event["data"]
        if detection.type == "bicycle":
            logger.info(title="[EVENT] New Bicycle Detected")
            detection.identity_id = None
            detection.plate_number = "N/A"
            detection.is_strange = False
            detection.is_recognized = True
            detection.is_processing = False

            state_manager.update(detection)
            return

        frame_image = event["frame"].get_image()
        x, y, w, h = detection.bbox

        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        vehicle_crop = frame_image[y1:y2, x1:x2, :]

        plates = plate_recognitor.detect_license_plates(vehicle_crop)

        frame_image_path = (
            "src/modules/server/front_end/react/public/"
            f"frame_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        frame_image_name = os.path.basename(frame_image_path)

        if len(plates) == 0:
            logger.info(
                title="Alert: Unknown Vehicle - No Plate Read",
                system_label=f"License plate scan failed (Track ID={detection.tracker_id}).",
                file_path=frame_image_name,
                visual_detail="",
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

        detection.identity_id = identity_id
        detection.plate_number = plate_number
        detection.confidence = score
        detection.type = detection.type
        detection.is_strange = identity_id is None or plate_number == "Unknown"

        detection.is_recognized = True
        detection.is_processing = False

        if detection.is_strange:
            logger.info(
                title=f"Detected: Unknown Vehicle ({plate_number})",
                system_label=f"Vehicle is not registered (Track ID={detection.tracker_id}).",
            )
        else:
            logger.info(
                title=f"Verified: Registered Vehicle ({plate_number})",
                system_label=f"Vehicle found in registry (ID={identity_id}).",
            )

        state_manager.update(detection)

    return handler
