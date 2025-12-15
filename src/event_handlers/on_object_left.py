from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from src.modules.alerts.alert_service import AlertService
from src.utils.classes import Detection
import datetime

def on_object_left(alert_service: AlertService, logger: Logger, state_manager: StateManager):

    def handler(event):
        det: Detection = event["data"]
        frame = event["frame"].get_image()
        
        if det.type == 'person':
            if det.is_strange:
                logger.info(f"[EVENT] Người lạ ID {det.tracker_id} rời khỏi khu vực.")
                
                if not state_manager.is_any_stranger():
                    logger.info(f"[EVENT] Không còn người lạ nào trong khu vực.")
                    alert_service.stop_alarm_sound()
            else:
                logger.info(f"[EVENT] {det.name} rời khỏi khu vực.")
        elif det.type == 'bicycle':
            logger.info(f"[EVENT] Xe đạp rời khỏi khu vực.")
        else:
            logger.info(f"[EVENT] {det.type} biển số {det.plate_number} rời khỏi khu vực.")

    return handler