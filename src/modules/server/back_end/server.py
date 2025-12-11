from flask import Flask, Response,  request, jsonify
import threading
import time
import os
from dotenv import load_dotenv
from ...camera.camera import Camera
from ..back_end.app.controllers.SendCameraLiveModules import SendCameraLiveModules
from ..back_end.app.controllers.SendLogsModules import SendLogsModules
from ..back_end.app.controllers.SendRecordsCameraModules import SendRecordsCameraModules
from ..back_end.app.controllers.LongPollingModules import LongPollingModules
from .app.modules.DataType import AlertData
from flask_cors import CORS



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

@app.route('/video')
def video_feed():
    cam = Camera(source="data/test_vid.mp4")
    if cam is not None:
        module = SendCameraLiveModules(lambda: provider(cam=cam))
        return Response(module.gen_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Error: cant get camera live because camera is None"

@app.route('/logs', methods=['GET'])
def sendLogs():
    log_module = SendLogsModules()
    logs = log_module.getLogs()
    print(logs, type(logs))
    return logs

@app.route('/video_records')
def sendVideoRecords():
    recorded_videos_folder_path = static_path + "/video"
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
            time.sleep(10)
            print("check current client id: ", current_client_id)
            if current_client_id is not None:
                #sau đó dựa vào id của client + truyền thông báo dưới dạng AlertData để thông báo cho clients
                long_polling.sendMsgToClient(current_client_id, AlertData(id=index, ms="Detect stranger!"))
            
            index += 1
        else:
            time.sleep(0.1)


if __name__ == "__main__":
    threading.Thread(target=detect_stranger, daemon=True).start()
    app.run(host="127.0.0.1", port=5000)

    


