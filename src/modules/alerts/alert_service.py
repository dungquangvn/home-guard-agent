import threading
import winsound
import smtplib
from email.message import EmailMessage
import cv2
from datetime import datetime
import requests
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
import datetime, base64
from dotenv import load_dotenv
load_dotenv()

class AlertService:
    def __init__(self):
        self.config = {
            "sender_email": "homeguardagent.int3412e@gmail.com",    # Thay bằng email test nếu muốn
            "receiver_email": "lannguyen51281@gmail.com",
            "audio_path": "data/loud_alarm.wav",           # Đảm bảo đường dẫn đúng hoặc file tồn tại
            "log_file_path": "logs/test_alert_log.txt"  # File log riêng cho lúc test
        }
        self._alarm_playing = False
        self._lock = threading.Lock()

    # =========================
    # 🔊 ALARM SOUND
    # =========================
    def start_alarm_sound(self, loop=False):
        """Phát còi báo động (non-block, chỉ 1 instance)."""
        with self._lock:
            if self._alarm_playing:
                return

            self._alarm_playing = True
            
        flags = winsound.SND_FILENAME | winsound.SND_ASYNC
        if loop:
            flags |= winsound.SND_LOOP

        winsound.PlaySound(
            self.config["audio_path"],
            flags
        )

    def stop_alarm_sound(self):
        """Dừng còi báo động."""
        with self._lock:
            if not self._alarm_playing:
                return

            self._alarm_playing = False

        winsound.PlaySound(None, winsound.SND_PURGE)

    def send_email(self, subject, html_content, image_path: str):
        from_email = self.config["sender_email"]
        to_email = self.config["receiver_email"]
        threading.Thread(
            target=self._send_email,
            args=(from_email, to_email, subject, html_content, image_path),
            daemon=True
        ).start()

    def _send_email(self, from_email, to_email, subject, html_content, image_path: str):
        try:
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            message.attachment = [
                self._image_to_attachment(image_path, "alert_frame"),
            ]
            response = sg.send(message)

            if response.status_code != 202:
                print("[EMAIL ERROR]", response.status_code)
            else:
                print("[EMAIL SENT] Alert email sent successfully.")

        except Exception as e:
            print("[EMAIL EXCEPTION]", e)
            
    def _image_to_attachment(self, image_path: str, cid: str):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        return Attachment(
            file_content=FileContent(encoded),
            file_type=FileType("image/jpeg"),
            file_name=FileName(image_path),
            disposition=Disposition("inline"),
            content_id=ContentId(cid)
        )