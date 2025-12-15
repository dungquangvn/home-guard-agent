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
                logger.info(
                    title="[EVENT] Người lạ rời khỏi khu vực",
                    message=f"Người lạ (ID={det.tracker_id})"
                )
                
                if not state_manager.is_any_stranger():
                    logger.info(
                        title="[EVENT] Khu vực đã an toàn",
                        message="Không còn người lạ trong khu vực giám sát."
                    )
                    alert_service.stop_alarm_sound()
            else:
                logger.info(
                    title="[EVENT] Người quen rời khỏi khu vực",
                    message=f"{det.name} (ID={det.tracker_id})"
                )
        elif det.type == 'bicycle':
            logger.info(
                title="[EVENT] Xe đạp rời khỏi khu vực",
                message=f"Xe đạp (Track ID={det.tracker_id})"
            )
        else:
            logger.info(
                title="[EVENT] Xe rời khỏi khu vực",
                message=f"Xe với biển số {det.plate_number} (ID={det.identity_id})"
            )

    return handler