import os
import threading
from datetime import datetime
import json
import uuid

class Logger:
    # ... (giữ nguyên __init__ và các thuộc tính khác)

    def __init__(self, log_file="system.log", auto_flush=True):
        self.log_file = log_file
        self.auto_flush = auto_flush
        self.lock = threading.Lock()
        
        # Thêm thuộc tính để lưu trữ Metadata của log (title/description mapping)
        self.log_metadata = {
            "info": {"title": "INFO", "description": "General Information"},
            "warning": {"title": "WARNING", "description": "System Warning"},
            "error": {"title": "ERROR", "description": "Application Error"},
            "debug": {"title": "DEBUG", "description": "Debugging Message"}
        }

        # os.makedirs(self.log_file, exist_ok=True)
        
    # Sửa đổi hàm _write để tạo LogsData và ghi JSON
    def _write(self, level, message, custom_title=None, custom_desc=None, file_path=None):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Lấy metadata hoặc dùng giá trị mặc định
        metadata = self.log_metadata.get(level.lower(), {"title": level.upper(), "description": "Custom Event"})
        
        # 1. Tạo đối tượng LogsData (dưới dạng dictionary)
        log_data_entry = {
            "id": str(uuid.uuid4()), # Tạo ID duy nhất
            "title": custom_title if custom_title else metadata["title"],
            "description": custom_desc if custom_desc else message, # Dùng message làm description
            "time": timestamp,
            "file_path": file_path if file_path else ""
        }

        # 2. Chuyển LogsData thành chuỗi JSON và thêm ký tự xuống dòng
        json_line = json.dumps(log_data_entry, ensure_ascii=False) + "\n"

        # 3. Ghi chuỗi JSON vào file (mỗi log là 1 dòng JSON)
        with self.lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json_line)
                if self.auto_flush:
                    f.flush()

    # Cập nhật các hàm gọi log
    def info(self, message, title="INFO", file_path=None):
        self._write("info", message, custom_title=title, file_path=file_path)

    def warning(self, message, title="WARNING", file_path=None):
        self._write("warning", message, custom_title=title, file_path=file_path)

    def error(self, message, title="ERROR", file_path=None):
        self._write("error", message, custom_title=title, file_path=file_path)
        
    def debug(self, message, title="DEBUG", file_path=None):
        self._write("debug", message, custom_title=title, file_path=file_path)
