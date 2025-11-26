import smtplib
import cv2
import os
import asyncio
import logging
from email.message import EmailMessage
from datetime import datetime
from typing import Dict, Any

# Kiểm tra thư viện âm thanh
try:
    import simpleaudio as sa 
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[ALERT WARNING] Thư viện 'simpleaudio' chưa được cài đặt.")

class AlertService:
    def __init__(self, config: Dict[str, str], event_bus=None):
        """
        config: Dict chứa cấu hình email, audio_path và log_file_path
        """
        self.config = config
        self.logger = logging.getLogger("AlertService")
        self.is_playing_audio = False
        
        # Đường dẫn file log txt (Mặc định lưu vào thư mục data nếu không cấu hình)
        self.log_file_path = config.get("log_file_path", "data/alert_history.txt")

        # Tạo thư mục chứa log nếu chưa có
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

        if event_bus:
            event_bus.on("alert_required", self.on_alert_requested)

    async def on_alert_requested(self, data: Dict[str, Any]):
        """Handler chính nhận sự kiện."""
        self.logger.info(f"Nhận yêu cầu cảnh báo ID: {data.get('track_id')}")
        loop = asyncio.get_event_loop()
        
        tasks = []
        
        # 1. Tác vụ: Ghi file TXT (Mới thêm)
        tasks.append(loop.run_in_executor(None, self._write_to_file_sync, data))

        # 2. Tác vụ: Phát âm thanh
        tasks.append(loop.run_in_executor(None, self._play_sound_sync))
        
        # 3. Tác vụ: Gửi Email
        frame_copy = data.get('frame').copy() if data.get('frame') is not None else None
        tasks.append(loop.run_in_executor(None, self._send_email_sync, data, frame_copy))

        # Chạy tất cả cùng lúc
        await asyncio.gather(*tasks)

    def _write_to_file_sync(self, info: Dict[str, Any]):
        """Ghi thông tin cảnh báo vào file txt."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            track_id = info.get('track_id', 'N/A')
            label = info.get('label', 'Unknown')
            message = info.get('message', '')
            
            log_line = f"[{timestamp}] ID: {track_id} | Label: {label} | Msg: {message}\n"
            
            # Mở file mode 'a' (append) để ghi thêm vào cuối file
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_line)
                
            print(f"[LOG] Đã ghi cảnh báo vào file: {self.log_file_path}")
            
        except Exception as e:
            self.logger.error(f"Lỗi ghi file log: {e}")

    def _play_sound_sync(self):
        """Phát âm thanh cảnh báo."""
        if self.is_playing_audio: 
            return

        audio_path = self.config.get("audio_path", "data/alerts.wav")
        
        if AUDIO_AVAILABLE and os.path.exists(audio_path):
            try:
                self.is_playing_audio = True
                wave_obj = sa.WaveObject.from_wave_file(audio_path)
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                self.logger.error(f"Lỗi phát âm thanh: {e}")
            finally:
                self.is_playing_audio = False
        else:
            # Chỉ in ra màn hình nếu không có file âm thanh (đỡ ồn khi test log)
            print(">>> BEEP BEEP (Sound simulation) <<<")

    def _send_email_sync(self, info: Dict[str, Any], frame):
        """Gửi email cảnh báo."""
        sender = self.config.get('sender_email')
        password = self.config.get('sender_password')
        receiver = self.config.get('receiver_email')

        if not sender or not password:
            # Nếu đang test log file, có thể user chưa điền email, bỏ qua không báo lỗi
            return

        try:
            msg = EmailMessage()
            msg['Subject'] = f"[HOME GUARD] CẢNH BÁO: {info.get('label')}"
            msg['From'] = sender
            msg['To'] = receiver
            msg.set_content(f"Phát hiện lúc {datetime.now()}\nID: {info.get('track_id')}")

            if frame is not None:
                is_success, buffer = cv2.imencode(".jpg", frame)
                if is_success:
                    msg.add_attachment(buffer.tobytes(), maintype='image', subtype='jpg', filename='alert.jpg')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)
            self.logger.info(f"Đã gửi email tới {receiver}")
        except Exception as e:
            self.logger.error(f"Lỗi gửi email: {e}")


if __name__ == "__main__":
    # === THÊM ĐOẠN NÀY VÀO ĐẦU ===
    import sys
    # Thiết lập encoding là utf-8 để in được tiếng Việt trên Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8') 
    except Exception:
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except Exception:
            pass
    
    
    import numpy as np 
    
    # 1. Cấu hình giả lập (Điền email thật nếu muốn test gửi mail, hoặc để trống để test log)
    test_config = {
        "sender_email": "",    # Thay bằng email test nếu muốn
        "sender_password": "",   # App password
        "receiver_email": "",
        "audio_path": "data/alerts.wav",           # Đảm bảo đường dẫn đúng hoặc file tồn tại
        "log_file_path": "data/test_alert_log.txt"  # File log riêng cho lúc test
    }

    # 2. Tạo dữ liệu giả lập (Mock data) giống output của model
    # Tạo một ảnh màu đen kích thước 640x480
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    test_data = {
        "track_id": 999,
        "label": "TEST_OBJECT",
        "message": "Đây là tin nhắn kiểm thử từ main block",
        "frame": dummy_frame,
        "timestamp": datetime.now()
    }

    # 3. Hàm chạy test async
    async def run_test():
        print("--- BẮT ĐẦU TEST MODULE ALERTS ---")
        
        # Khởi tạo service
        service = AlertService(test_config)
        
        # Gọi hàm xử lý (giả lập việc EventBus gọi hàm này)
        print(f"Đang gửi cảnh báo vào file: {test_config['log_file_path']}...")
        await service.on_alert_requested(test_data)
        
        print("--- KẾT THÚC TEST ---")
        print(f"Vui lòng kiểm tra file '{test_config['log_file_path']}'")

    # 4. Thực thi
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass