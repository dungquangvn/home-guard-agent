from flask import Flask, Response, render_template_string
import threading
import time
import cv2
import os
from dotenv import load_dotenv
from ...camera.camera import Camera
from ..back_end.app.controllers.SendCameraLiveModules import SendCameraLiveModules
from ..back_end.app.controllers.SendLogsModules import SendLogsModules
from ..back_end.app.controllers.SendRecordsCameraModules import SendRecordsCameraModules
from flask_cors import CORS


#set up
load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")
static_path = os.getenv("BACK_END_STATIC_FOLDER_URL")

app = Flask(__name__, static_folder="static", static_url_path="/static")

CORS(app)

# Router

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

# Utilitizes functions

def run_server(host='0.0.0.0', port=5000):
    app.run(host=host, port=port, threaded=True)


def provider(cam: Camera):
    frame = cam.get_frame()
    if frame is None:
        return None
    return frame.image

#Test

if __name__ == "__main__":
    print("Run main")

    server_thread = threading.Thread(
        target=run_server,
        kwargs={'host': host, 'port': port},
        daemon=False
    )

    server_thread.start()
    server_thread.join()

