import os
import threading
from datetime import datetime

class Logger:
    def __init__(self, log_file="logs/system.log", auto_flush=True):
        self.log_file = log_file
        self.auto_flush = auto_flush
        self.lock = threading.Lock()

        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def _write(self, level, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{now}] [{level.upper()}] {message}\n"

        with self.lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
                if self.auto_flush:
                    f.flush()

    def info(self, message):
        self._write("info", message)

    def warning(self, message):
        self._write("warning", message)

    def error(self, message):
        self._write("error", message)
        
    def debug(self, message):
        self._write("debug", message)
