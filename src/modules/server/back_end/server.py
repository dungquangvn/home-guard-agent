from flask import Flask, Response, request, jsonify
import threading
import time
import os
import cv2
from dotenv import load_dotenv
from src.modules.server.back_end.app.controllers.SendLogsModules import SendLogsModules
from src.modules.server.back_end.app.controllers.SendRecordsCameraModules import SendRecordsCameraModules
from src.modules.server.back_end.app.controllers.LongPollingModules import LongPollingModules
from src.modules.security_chat.rag import answer_log_query
from .app.modules.DataType import AlertData
from flask_cors import CORS
from multiprocessing import Queue

# Global shared objects (injected by start_server)
frame_queue = None
shared_brightness_value = None
shared_stats_value = None
active_stream_clients = 0

# Setup
load_dotenv()
static_path = os.getenv("BACK_END_STATIC_FOLDER_URL")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)
current_client_id = None


@app.route("/")
def index():
    return "Server is running!"


@app.route("/video")
def video_feed():
    """MJPEG video endpoint."""
    global active_stream_clients

    if frame_queue is None:
        return "Queue not initialized!", 500

    def gen():
        global active_stream_clients

        active_stream_clients += 1
        stream_frames_window = 0
        last_stats_at = time.perf_counter()

        if shared_stats_value is not None:
            shared_stats_value["active_stream_clients"] = int(active_stream_clients)

        try:
            while True:
                try:
                    frame = frame_queue.get(timeout=0.05)
                except Exception:
                    time.sleep(0.001)
                    continue

                ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    continue

                frame_bytes = jpeg.tobytes()
                stream_frames_window += 1

                now = time.perf_counter()
                elapsed_stats = now - last_stats_at
                if shared_stats_value is not None and elapsed_stats >= 1.0:
                    shared_stats_value["stream_fps"] = float(stream_frames_window / elapsed_stats)
                    shared_stats_value["active_stream_clients"] = int(active_stream_clients)
                    shared_stats_value["updated_at"] = time.time()
                    stream_frames_window = 0
                    last_stats_at = now

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
        finally:
            active_stream_clients = max(0, active_stream_clients - 1)
            if shared_stats_value is not None:
                shared_stats_value["active_stream_clients"] = int(active_stream_clients)

    return Response(
        gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/stream_stats", methods=["GET"])
def get_stream_stats():
    if shared_stats_value is None:
        return jsonify({"error": "Stream stats not initialized"}), 500

    return jsonify(
        {
            "source_fps": round(float(shared_stats_value.get("source_fps", 0.0)), 2),
            "processing_fps": round(float(shared_stats_value.get("processing_fps", 0.0)), 2),
            "stream_fps": round(float(shared_stats_value.get("stream_fps", 0.0)), 2),
            "dropped_frames_total": int(shared_stats_value.get("dropped_frames_total", 0)),
            "active_stream_clients": int(shared_stats_value.get("active_stream_clients", 0)),
            "source_type": str(shared_stats_value.get("source_type", "unknown")),
            "updated_at": float(shared_stats_value.get("updated_at", time.time())),
        }
    )


@app.route("/logs", methods=["GET"])
def send_logs():
    log_module = SendLogsModules()
    return log_module.getLogs()


@app.route("/video_records")
def send_video_records():
    recorded_videos_folder_path = static_path + "/video_record"
    video_record_module = SendRecordsCameraModules(recorded_videos_folder_path)
    return video_record_module.getVideoRecords()


@app.route("/security_chat/query", methods=["POST"])
def query_security_chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    start_time = str(payload.get("start_time", "")).strip() or None
    end_time = str(payload.get("end_time", "")).strip() or None

    if not question:
        return jsonify({"error": "question is required"}), 400

    top_k = payload.get("top_k", 6)
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 6
    top_k = max(1, min(top_k, 12))

    result = answer_log_query(
        user_query=question,
        top_k=top_k,
        start_time=start_time,
        end_time=end_time,
    )
    return jsonify(result)


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
        except Exception:
            time.sleep(0.1)

    return jsonify({"has_message": False, "message": None})


@app.route("/brightness", methods=["GET"])
def get_brightness():
    if shared_brightness_value is None:
        return jsonify({"error": "Brightness value not initialized"}), 500

    avg_brightness = shared_brightness_value.get()
    return jsonify(
        {
            "avg_brightness": round(avg_brightness, 2),
            "timestamp": time.time(),
        }
    )


def detect_stranger():
    index = 0
    long_polling = LongPollingModules()

    while True:
        if not long_polling.isNotHavingClients():
            time.sleep(30)
            if current_client_id is not None:
                long_polling.sendMsgToClient(
                    current_client_id, AlertData(id=index, ms="Detect stranger!")
                )
            index += 1
        else:
            time.sleep(0.1)


def start_server(queue: Queue, brightness_value, stats_value=None, host="127.0.0.1", port=5000):
    """Run Flask server in a separate process."""
    global frame_queue
    global shared_brightness_value
    global shared_stats_value

    frame_queue = queue
    shared_brightness_value = brightness_value
    shared_stats_value = stats_value

    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=detect_stranger, daemon=True).start()
    app.run(host="127.0.0.1", port=5000)
