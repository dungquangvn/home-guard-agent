from flask import jsonify
from ..modules.DataType import LogsData
import os
import json

LOG_FILE_PATH = "logs/system.log"


class SendLogsModules:
    __instance = None
    __isInitialized = False
    __logs = []
    __last_modified_time = 0 # Thêm thuộc tính lưu thời gian sửa đổi file

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
        
    def __init__(self):
        if not self.__isInitialized: 
            self.__isInitialized = True
            
    def _read_logs_from_file(self):
        """Hàm đọc tất cả log từ file JSON Line-by-Line."""
        new_logs = []
        if not os.path.exists(LOG_FILE_PATH):
            return new_logs

        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    # Đọc mỗi dòng là 1 đối tượng JSON
                    if line.strip(): # Bỏ qua dòng trống
                        log_dict = json.loads(line)
                        # Chuyển dictionary thành đối tượng LogsData
                        new_logs.append(LogsData(**log_dict)) 
            return new_logs
        except Exception as e:
            print(f"Error reading or parsing log file: {e}")
            return []


    def getLogs(self):
        # 1. Kiểm tra sự thay đổi của file
        if os.path.exists(LOG_FILE_PATH):
            current_modified_time = os.path.getmtime(LOG_FILE_PATH)
            
            # Nếu thời gian sửa đổi file đã thay đổi (hoặc là lần đầu tiên đọc)
            if current_modified_time > self.__last_modified_time:
                print("Log file changed. Reloading logs...")
                
                # Cập nhật thời gian sửa đổi
                self.__last_modified_time = current_modified_time
                
                # Tải lại logs
                self.__logs = self._read_logs_from_file()
            else:
                print("Log file not changed. Using cached logs.")
        else:
            # File không tồn tại
            self.__logs = []
            self.__last_modified_time = 0


        # 2. Chuyển đổi danh sách đối tượng LogsData thành định dạng có thể jsonify
        # Dùng list comprehension để chuyển về dict trước khi jsonify
        logs_for_json = [log.__dict__ for log in self.__logs] 
        
        return jsonify(logs_for_json)

