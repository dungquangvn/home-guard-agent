import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import copy
import time
import argparse
import threading
from queue import Queue as ThreadQueue, Empty, Full

import cv2
from ultralytics import YOLO

from src.modules.camera.camera import Camera
from src.modules.alerts.alert_service import AlertService
from src.modules.logging.logger import Logger
from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.recognition.plate_recognitor import CustomLicensePlateRecognizer
from src.modules.video_recorder.video_recorder import VideoRecorder, EventVideoRecorder
from src.modules.caption_generator.caption_generator import CaptionGenerator
from src.core.event_extractor import EventExtractor
from src.core.event_bus import EventBus
from src.core.state_manager import StateManager
from src.event_handlers.on_new_person import on_new_person
from src.event_handlers.on_new_vehicle import on_new_vehicle
from src.event_handlers.on_object_left import on_object_left
from src.event_handlers.on_stranger_stay_long import on_stranger_stay_long
from src.utils.classes import FrameData

ELAPSED_STATS_PERIOD = 2


class LocalSharedValue:
    def __init__(self, value):
        self._value = value

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

def _build_ai_pipeline():
    tracker = YOLO("models/yolo11n.pt").to("cuda")

    face_recognitor = FaceRecognitor(face_db_path="models/face_db.pkl", sim_threshold=0.32)
    caption_generator = CaptionGenerator()
    plate_recognitor = CustomLicensePlateRecognizer(threshold_conf=0.1)
    alert_service = AlertService()
    logger = Logger()

    state_manager = StateManager(logger)
    event_extractor = EventExtractor(state_manager)
    event_bus = EventBus()

    event_bus.on(
        "new_person",
        on_new_person(face_recognitor, caption_generator, alert_service, logger, state_manager),
    )
    event_bus.on("new_vehicle", on_new_vehicle(plate_recognitor, logger, state_manager))
    event_bus.on("object_left", on_object_left(alert_service, logger, state_manager))

    return tracker, state_manager, event_extractor, event_bus, logger, alert_service


def _camera_loop(
    cam: Camera,
    stream_queue: ThreadQueue,
    ai_process_queue: ThreadQueue,
    stop_event: threading.Event,
    detections_state: dict,
    detections_lock: threading.Lock,
    video_recorder: VideoRecorder,
    event_recorder: EventVideoRecorder,
    stats_value,
):
    '''
    Loop bên ngoài, loop qua từng frame của camera và đặt vào ai_process_queue, lấy detection mới nhất và vẽ cho stream_queue
    
    :param stream_queue: Queue để gửi frame đã vẽ detections cho Flask server
    :param ai_process_queue: Queue để gửi frame gốc cho thread ai_process
    :param detections_state: lưu kết quả detection hiện tại
    '''
    source_fps = cam.fps
    time_per_frame = 1.0 / source_fps
    stream_start = time.perf_counter()
    produced_frames = 0
    dropped_for_timing = 0
    dropped_ai_process_queue = 0
    last_stats_at = time.perf_counter()

    while not stop_event.is_set():
        if cam.is_file_source:
            elapsed = time.perf_counter() - stream_start
            expected_frames = int(elapsed / time_per_frame)
            frames_behind = expected_frames - produced_frames
            if frames_behind > 0:
                dropped_now = cam.drop_frames(frames_behind)
                produced_frames += dropped_now
                dropped_for_timing += dropped_now

        frame_data = cam.get_frame()
        if frame_data is None:
            stop_event.set()
            break
        produced_frames += 1

        to_be_processed_frame = FrameData(frame_id=frame_data.frame_id, image=frame_data.image.copy())
        # Nếu ai_process_queue đã đầy, loại bỏ frame cũ nhất để nhường chỗ cho frame mới
        if ai_process_queue.full():
            try:
                ai_process_queue.get_nowait()
                dropped_ai_process_queue += 1
            except Empty:
                pass
        # Đặt frame mới vào ai_process_queue, ai_process_loop sẽ lấy frame từ queue này để xử lý
        try:
            ai_process_queue.put_nowait(to_be_processed_frame)
        except Full:
            dropped_ai_process_queue += 1

        display_frame = frame_data.image.copy()
        display_frame_data = FrameData(frame_id=frame_data.frame_id, image=display_frame)
        # Đọc kết quả detection do ai_process_loop ghi vào hiện tại
        # Dùng lock do biến này vừa ghi bởi ai_process_loop vừa đọc ở đây
        with detections_lock:
            detections_snapshot = detections_state["detections"]

        # Vẽ các detection đọc được lên frame
        for det in detections_snapshot:
            display_frame_data.add_object(det)

        next_deadline = stream_start + produced_frames * time_per_frame
        remaining = next_deadline - time.perf_counter()
        if remaining > 0:
            time.sleep(remaining)

        # Đặt frame đã vẽ vào stream_queue
        try:
            while not stream_queue.empty():
                stream_queue.get_nowait()
            stream_queue.put_nowait(display_frame_data.image)
        except Exception:
            pass

        video_recorder.write(display_frame_data.image)
        event_recorder.push(display_frame_data.image)

        now = time.perf_counter()
        elapsed_stats = now - last_stats_at
        if elapsed_stats >= ELAPSED_STATS_PERIOD:
            stats_value["source_fps"] = float(source_fps)
            stats_value["dropped_frames_total"] = int(dropped_for_timing + dropped_ai_process_queue)
            stats_value["source_type"] = "video_file" if cam.is_file_source else "live_camera"
            stats_value["updated_at"] = time.time()
            last_stats_at = now


def _ai_process_loop(
    ai_process_queue: ThreadQueue,
    stop_event: threading.Event,
    brightness_value,
    detections_state: dict,
    detections_lock: threading.Lock,
    stats_value,
    event_recorder: EventVideoRecorder,
):
    (
        tracker,
        state_manager,
        event_extractor,
        event_bus,
        logger,
        alert_service,
    ) = _build_ai_pipeline()

    event_bus.on("stranger_stay_long", on_stranger_stay_long(alert_service, event_recorder, logger))

    processed_frames_window = 0
    last_stats_at = time.perf_counter()

    while not stop_event.is_set() or not ai_process_queue.empty():
        try:
            frame_data = ai_process_queue.get(timeout=0.1)
        except Empty:
            continue

        if frame_data.get_id() % 3 == 1:
            results = tracker.track(
                frame_data.get_image(),
                device=0,
                persist=True,
                tracker="tracker_config.yaml",
                conf=0.35,
                iou=0.3,
                classes=[0, 1, 2, 3],
                verbose=False,
            )

            events = event_extractor.extract(results)
            for evt in events:
                evt["frame"] = frame_data
            event_bus.emit(events)

            gray = cv2.cvtColor(frame_data.image, cv2.COLOR_BGR2GRAY)
            avg_brightness = float(gray.mean())
            brightness_value.set(avg_brightness)

        tracked_dets = state_manager.get_current_detections()
        with detections_lock:
            detections_state["detections"] = copy.deepcopy(list(tracked_dets.values()))

        processed_frames_window += 1
        now = time.perf_counter()
        elapsed_stats = now - last_stats_at
        if elapsed_stats >= ELAPSED_STATS_PERIOD:
            stats_value["processing_fps"] = float(processed_frames_window / elapsed_stats)
            stats_value["updated_at"] = time.time()
            processed_frames_window = 0
            last_stats_at = now


def main(camera_source, stream_queue: ThreadQueue, brightness_value, stats_value):
    '''
    camera_thread loop từng frame từ camera, đặt vào ai_process_queue (nếu queue đầy thì drop frame)
    ai_process_thread lấy từ queue này để xử lý và sửa các biến share (detection, stats...)
    camera_thread lấy giá trị mới nhất của biến share vẽ lên frame và truyền cho stream_queue, đảm bảo fps live feed
    '''
    
    cam = Camera(source=camera_source)

    video_recorder = VideoRecorder(
        fps=cam.fps,
        width=cam.width,
        height=cam.height,
    )
    event_recorder = EventVideoRecorder(
        buffer_seconds=10,
        fps=cam.fps,
        width=cam.width,
        height=cam.height,
    )

    ai_process_queue = ThreadQueue(maxsize=8)
    stop_event = threading.Event()
    detections_lock = threading.Lock()
    detections_state = {"detections": []}

    ai_process_thread = threading.Thread(
        target=_ai_process_loop,
        args=(
            ai_process_queue,
            stop_event,
            brightness_value,
            detections_state,
            detections_lock,
            stats_value,
            event_recorder,
        ),
        daemon=True,
    )

    camera_thread = threading.Thread(
        target=_camera_loop,
        args=(
            cam,
            stream_queue,
            ai_process_queue,
            stop_event,
            detections_state,
            detections_lock,
            video_recorder,
            event_recorder,
            stats_value,
        ),
        daemon=True,
    )

    ai_process_thread.start()
    camera_thread.start()

    try:
        camera_thread.join()
    finally:
        stop_event.set()
        ai_process_thread.join(timeout=5.0)
        video_recorder.release()
        cam.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", 
        type=lambda x: int(x) if x.isdigit() else x,
        default=0,
        help="Đường dẫn đến vid"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Bật chế độ debug'
    )
    args = parser.parse_args()
    if args.debug:
        os.environ["VEHICLE_OCR_DEBUG"] = "1"
        print("[DEBUG] Vehicle OCR debug is enabled (VEHICLE_OCR_DEBUG=1).")

    frame_queue = ThreadQueue(maxsize=1)
    shared_brightness = LocalSharedValue(0.0)
    shared_stats = dict(
        {
            "source_fps": 0.0,
            "processing_fps": 0.0,
            "stream_fps": 0.0,
            "dropped_frames_total": 0,
            "active_stream_clients": 0,
            "source_type": "unknown",
            "updated_at": time.time(),
        }
    )

    try:
        print("Running AI pipeline only. Backend server is not started from main.py.")
        main(args.source, frame_queue, shared_brightness, shared_stats)
    except KeyboardInterrupt:
        print("Stopping main process...")
    print("Application stopped.")
