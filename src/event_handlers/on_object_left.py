from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from src.modules.alerts.alert_service import AlertService
from src.utils.classes import Detection

STRANGER_LEFT_MIN_SEEN_SECONDS = 3.0


def on_object_left(alert_service: AlertService, logger: Logger, state_manager: StateManager):

    def handler(event):
        det: Detection = event["data"]
        _frame = event["frame"].get_image()

        if det.type == "person":
            # Skip noisy leave logs while identity is still unstable.
            if det.recognition_state in ["pending", "collecting"]:
                return

            seen_duration = max(0.0, float(det.last_seen or 0.0) - float(det.first_seen or 0.0))
            is_confirmed_stranger = (
                det.recognition_state == "stable_unknown"
                and seen_duration >= STRANGER_LEFT_MIN_SEEN_SECONDS
            )

            if is_confirmed_stranger:
                logger.info(
                    title="Left Area: Unknown Person",
                    system_label=f"Unidentified subject left the monitored area (Track ID={det.tracker_id}).",
                )

                if not state_manager.is_any_stranger():
                    logger.info(
                        title="Status: Area Secure",
                        system_label="The last unknown subject has left the monitored area.",
                    )
                    alert_service.stop_alarm_sound()
            elif not det.is_strange:
                logger.info(
                    title=f"Left Area: {det.name}",
                    system_label=f"Registered member left the monitored area (Track ID={det.tracker_id}).",
                )
            # stable_unknown but too short -> skip by design.

        elif det.type == "bicycle":
            logger.info(
                title="Left Area: Bicycle",
                system_label=f"Non-motorized vehicle left the monitored area (Track ID={det.tracker_id}).",
            )
        else:
            logger.info(
                title=f"Left Area: Vehicle ({det.plate_number})",
                system_label=f"Motor vehicle left the monitored area (ID={det.identity_id}).",
            )

    return handler
