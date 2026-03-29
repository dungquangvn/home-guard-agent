from src.modules.logging.logger import Logger
from src.modules.alerts.alert_service import AlertService
from src.modules.video_recorder.video_recorder import EventVideoRecorder
from src.utils.classes import Detection
import datetime


def on_stranger_stay_long(alert_service: AlertService, event_recorder: EventVideoRecorder, logger: Logger):

    def handler(event):
        det: Detection = event["data"]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        video_name = f"event_{det.tracker_id}_{timestamp}.mp4"
        save_dir = "src/modules/server/front_end/react/public"

        event_recorder.save_event(save_dir, video_name)

        logger.warning(
            title="Alert: Unknown Person Staying Too Long",
            system_label=(
                "An unknown person is staying in the monitored area without any known person present "
                f"(Track ID={det.tracker_id})."
            ),
            file_path=video_name,
        )

        print("[EVENT] Unknown person stayed too long in monitored area. Alert emitted.")

    return handler


def build_email_html(det: Detection, image_cid="alert_frame") -> str:
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    html = f"""
    <html>
    <body style=\"font-family: Arial, sans-serif;\">
        <h2>Security Alert</h2>

        <p>
            Home Guard detected an <b>UNKNOWN PERSON</b>
            staying too long in the monitored area.
        </p>
        <p>Snapshot at alert time:</p>
        <img src=\"cid:{image_cid}\" style=\"max-width:100%;border:1px solid #ccc;\">

        <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
            <tr><td><b>Time</b></td><td>{now}</td></tr>
            <tr><td><b>Type</b></td><td>Person</td></tr>
            <tr><td><b>Track ID</b></td><td>{det.tracker_id}</td></tr>
            <tr><td><b>Confidence</b></td><td>{det.confidence:.2f}</td></tr>
            <tr><td><b>Status</b></td><td>Unknown</td></tr>
        </table>

        <p style=\"font-size:12px;color:#777;\">
            This email was sent automatically by Home Guard.
        </p>
    </body>
    </html>
    """
    return html
