from flask import jsonify
from ..modules.DataType import LogsData

class SendLogsModules:
    __instance = None
    __isInitialized = False
    __logs = []

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    def __init__(self):
        if not self.__isInitialized: 
            self.__isInitialized = True

    # Lấy logs từ file của server, nhớ kiểm tra xem liệu file có sự thay đổi không, 
    # nếu có thì truy xuất lại logs trong file và lưu vào biến static __logs của lớp này
    # nếu không thì không cần truy xuất lại logs trong file
    def getLogs(self):

        # ae viết code trích xuất dữ liệu từ file log ở đây
        # file logs ở server thì ae nên lưu dưới dạng mảng json nha
        # mảng json này thì sẽ gồm các đối tượng LogsData nha ae, ae xem ở path app/modules/DataType.py nha


        # phần dưới test cho ae 
        logs_data = [LogsData(id= "1", title="Camera Started", description="System boot OK", time="2025-12-05 10:21:00"),
                     LogsData(id= "2",title="Motion Detected", description="Movement at gate", time="2025-12-05 10:22:18")]

        self.__logs = logs_data

        return jsonify(self.__logs)

