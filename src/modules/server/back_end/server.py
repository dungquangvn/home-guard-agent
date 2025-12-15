from flask import Flask, Response,  request, jsonify
import threading
import time
import os
import cv2
from dotenv import load_dotenv
from src.modules.camera.camera import Camera
from src.modules.server.back_end.app.controllers.SendCameraLiveModules import SendCameraLiveModules
from src.modules.server.back_end.app.controllers.SendLogsModules import SendLogsModules
from src.modules.server.back_end.app.controllers.SendRecordsCameraModules import SendRecordsCameraModules
from src.modules.server.back_end.app.controllers.LongPollingModules import LongPollingModules
from .app.modules.DataType import AlertData
from flask_cors import CORS
import numpy as np
from multiprocessing import Queue, Process

# Biến toàn cục để lưu trữ Queue (sẽ được truyền vào khi chạy Process)
frame_queue = None

#set up
load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")
static_path = os.getenv("BACK_END_STATIC_FOLDER_URL")

app = Flask(__name__, static_folder="static", static_url_path="/static")

CORS(app)
current_client_id = None

# Router

#http
@app.route('/')
def index():
    return "Server is running!"

# @app.route('/video')
# def video_feed():
#     cam = Camera(source="data/test_vid.mp4")
#     if cam is not None:
#         module = SendCameraLiveModules(lambda: provider(cam=cam))
#         return Response(module.gen_mjpeg(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')
#     else:
#         return "Error: cant get camera live because camera is None"

@app.route('/video')
def video_feed():
    """Endpoint trả về video stream (Motion JPEG)."""
    
    # Kiểm tra Queue đã được thiết lập chưa
    if frame_queue is None:
        return "Queue not initialized!", 500

    def gen():
        while True:
            # Lấy frame mới nhất từ Queue. 
            # Dùng try-except để tránh lỗi nếu Queue trống
            try:
                # Dùng non-blocking get() với timeout ngắn
                # để server không bị chặn quá lâu
                frame = frame_queue.get(timeout=0.1) 
            except:
                # Nếu Queue trống, chờ một chút rồi thử lại
                time.sleep(0.03) 
                continue

            # Mã hóa frame (numpy array) sang JPEG
            _, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            # Trả về frame theo chuẩn Motion JPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # (Không cần time.sleep(0.03) ở đây vì tốc độ được kiểm soát 
            # bởi tốc độ frame được put vào Queue và tốc độ mạng)

    return Response(
        gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/logs', methods=['GET'])
def sendLogs():
    log_module = SendLogsModules()
    logs = log_module.getLogs()
    print(logs, type(logs))
    return logs

@app.route('/video_records')
def sendVideoRecords():
    recorded_videos_folder_path = static_path + "/video_record"
    video_record_module = SendRecordsCameraModules(recorded_videos_folder_path)
    return video_record_module.getVideoRecords()

@app.route("/poll")
def poll():
    global current_client_id
    client_id = request.args.get("client_id")
    current_client_id = client_id

    if client_id is None:
        return "Require client id!"

    long_polling = LongPollingModules()

    long_polling.addClientId(client_id)

    message_queue = long_polling.getLongPollingOfSpecifiedClient(client_id)
    
    timeout = 30 
    start = time.time()

    while time.time() - start < timeout:
        try:
            msg = message_queue.get_nowait()
            return jsonify({"has_message": True, "message": msg})
        except:
            time.sleep(0.1)
    
    return jsonify({"has_message": False, "message": None})


# Utilitizes functions


def provider(cam: Camera):
    frame = cam.get_frame()
    if frame is None:
        return None
    return frame.image

#Test cách gửi thông báo cho clients
def detect_stranger():
    index = 0

    #Dùng LongPollingModules
    long_polling = LongPollingModules()

    while True:
        if not long_polling.isNotHavingClients():
            time.sleep(30)
            print("check current client id: ", current_client_id)
            if current_client_id is not None:
                #sau đó dựa vào id của client + truyền thông báo dưới dạng AlertData để thông báo cho clients
                long_polling.sendMsgToClient(current_client_id, AlertData(id=index, ms="Detect stranger!"))
            
            index += 1
        else:
            time.sleep(0.1)

def start_server(queue: Queue, host='127.0.0.1', port=5000):
    """Hàm chạy Flask server trong một tiến trình riêng."""
    global frame_queue
    frame_queue = queue
    # Đặt use_reloader=False để tránh server chạy hai lần
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=detect_stranger, daemon=True).start()
    app.run(host="127.0.0.1", port=5000)