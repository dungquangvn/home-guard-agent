from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from src.modules.alerts.alert_service import AlertService
from src.utils.classes import Detection
from sendgrid.helpers.mail import *
import datetime, base64, os
import cv2

def on_stranger_stay_long(alert_service: AlertService, logger: Logger):

    def handler(event):
        det: Detection = event["data"]
        frame_image = event["frame"].get_image()
        if frame_image is None:
            print("[on_stranger_stay_long] No frame image available.")
        else:
            print("[on_stranger_stay_long] Frame image captured for alert.")
            print(frame_image.shape)
        frame_image_path = f'alert_frame_images/frame_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        os.makedirs('alert_frame_images', exist_ok=True)
        cv2.imwrite(frame_image_path, frame_image)

        logger.info(f"[EVENT] Người lạ (ID={det.tracker_id}) đứng lâu và trong khu vực không có người quen nào, phát cảnh báo và gửi mail cho chủ nhà.")
        alert_service.start_alarm_sound(loop=True)
        
        subject = "[HOME GUARD] ⚠️ CẢNH BÁO: Người lạ đứng lâu trước nhà "
        f"(Track ID #{det.tracker_id}"
        html = build_email_html(det, image_cid="alert_frame")
        content = Content("text/html", html)
        alert_service.send_email(subject, content, frame_image_path)

    return handler

def build_email_html(det: Detection, image_cid="alert_frame") -> str:
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>⚠️ CẢNH BÁO AN NINH</h2>

        <p>
            Hệ thống <b>Home Guard</b> phát hiện <b>NGƯỜI LẠ</b>
            đứng lâu trước khu vực giám sát.
        </p>
        <p>Hình ảnh tại thời điểm cảnh báo:</p>
        <img src="cid:{image_cid}" style="max-width:100%;border:1px solid #ccc;">

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <td><b>Thời gian</b></td>
                <td>{now}</td>
            </tr>
            <tr>
                <td><b>Loại đối tượng</b></td>
                <td>Người</td>
            </tr>
            <tr>
                <td><b>Track ID</b></td>
                <td>{det.tracker_id}</td>
            </tr>
            <tr>
                <td><b>Độ tin cậy nhận diện</b></td>
                <td>{det.confidence:.2f}</td>
            </tr>
            <tr>
                <td><b>Trạng thái</b></td>
                <td>Người lạ</td>
            </tr>
        </table>

        <p style="margin-top:10px;">
            📸 Hình ảnh đối tượng tại thời điểm cảnh báo được đính kèm trong email.
        </p>

        <p style="font-size:12px;color:#777;">
            Email này được gửi tự động bởi hệ thống Home Guard.
        </p>
    </body>
    </html>
    """
    return html