import argparse
import os
import time
from multiprocessing import Manager, Process, Queue

from main import main as run_ai_pipeline
from src.modules.server.back_end.server import start_server


def _parse_source(value: str):
    return int(value) if value.isdigit() else value


def _build_shared_objects():
    manager = Manager()
    frame_queue = Queue(maxsize=1)
    shared_brightness = manager.Value("f", 0.0)
    shared_stats = manager.dict(
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
    return manager, frame_queue, shared_brightness, shared_stats


def run(source, host, port, debug=False):
    if debug:
        os.environ["VEHICLE_OCR_DEBUG"] = "1"
        print("[DEBUG] Vehicle OCR debug is enabled (VEHICLE_OCR_DEBUG=1).")

    manager, frame_queue, shared_brightness, shared_stats = _build_shared_objects()
    backend_process = Process(
        target=start_server,
        args=(frame_queue, shared_brightness, shared_stats, host, port),
        daemon=True,
    )
    backend_process.start()

    try:
        print(f"Backend started at http://{host}:{port}")
        print("Running AI pipeline...")
        run_ai_pipeline(source, frame_queue, shared_brightness, shared_stats)
    except KeyboardInterrupt:
        print("Stopping processes...")
    finally:
        if backend_process.is_alive():
            backend_process.terminate()
            backend_process.join(timeout=5.0)
        if backend_process.is_alive():
            backend_process.kill()

        try:
            manager.shutdown()
        except Exception:
            pass

        print("Application stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run AI pipeline and backend server together (frontend runs separately)."
    )
    parser.add_argument(
        "--source",
        type=_parse_source,
        default=0,
        help="Camera index or video path (example: 0 or data/sample.mp4)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Backend host")
    parser.add_argument("--port", type=int, default=5000, help="Backend port")
    parser.add_argument("--debug", action="store_true", help="Enable OCR debug logs for new_vehicle handler")
    args = parser.parse_args()

    run(args.source, args.host, args.port, debug=args.debug)
