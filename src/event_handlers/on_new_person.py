from collections import defaultdict
from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.alerts.alert_service import AlertService
from src.modules.caption_generator.caption_generator import CaptionGenerator
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import os
import cv2
import datetime
import time

RECOGNITION_TIMEOUT = 5.0
CAPTION_TIMEOUT = 30.0
STABLE_RECOGNITION_WINDOW = 5
STABLE_RECOGNITION_MIN_VOTES = 3

executor = ThreadPoolExecutor(max_workers=3)


def _normalize_identity(identity_id, name):
    name_norm = (name or "Unknown").strip() or "Unknown"
    key_id = -1 if identity_id is None else identity_id
    return (key_id, name_norm.lower()), key_id, name_norm


def _get_stable_identity(history):
    """
    Nhận vào history recognition của 1 object
    - Đếm số vote và tổng score cho mỗi idenity_id
    - Trả về dict của idenity cao nhất
    
    :return: dict(
        key == identity_id or -1,
        idenity_id,
        name,
        score,
        votes,
    )
    """
    
    vote_map = defaultdict(lambda: {"count": 0, "score_sum": 0.0, "identity_id": None, "name": "Unknown"})

    for item in history:
        key, key_id, normalized_name = _normalize_identity(item.get("identity_id"), item.get("name"))
        vote_map[key]["count"] += 1
        vote_map[key]["score_sum"] += float(item.get("score", 0.0) or 0.0)
        vote_map[key]["identity_id"] = None if key_id == -1 else key_id
        vote_map[key]["name"] = normalized_name

    if not vote_map:
        return None

    best_key = None
    best_count = -1
    best_avg = -1.0
    for key, stats in vote_map.items():
        avg = stats["score_sum"] / max(stats["count"], 1)
        if stats["count"] > best_count or (stats["count"] == best_count and avg > best_avg):
            best_key = key
            best_count = stats["count"]
            best_avg = avg

    if best_count < STABLE_RECOGNITION_MIN_VOTES:
        return None

    stats = vote_map[best_key]
    avg_score = stats["score_sum"] / max(stats["count"], 1)
    return {
        "key": best_key,
        "identity_id": stats["identity_id"],
        "name": stats["name"],
        "score": avg_score,
        "votes": stats["count"],
    }


def on_new_person(
    face_recognitor: FaceRecognitor,
    caption_generator: CaptionGenerator,
    alert_service: AlertService,
    logger: Logger,
    state_manager: StateManager,
):
    """
    Handler cho event "new_person". Called periodically.

    Event format:
    {
        "event": "new_person",
        "data": Detection,
        "frame": FrameData
    }
    """

    def handler(event):
        detection = event["data"]
        previous_name = detection.name
        previous_stable_identity_key = detection.stable_identity_key

        frame_image = event["frame"].get_image()
        x, y, w, h = detection.bbox

        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        human_image = frame_image[y1:y2, x1:x2, :]

        face_future = executor.submit(face_recognitor.recognize_faces, [human_image])
        try:
            people = face_future.result(timeout=RECOGNITION_TIMEOUT)
            identity_id = people[0]["identity_id"]
            name = people[0]["name"]
            score = people[0]["score"]
        except TimeoutError:
            face_future.cancel()
            identity_id = None
            name = "Unknown"
            score = 0.0

        # Lưu lại 5 kết quả recognition gần nhất để vote
        detection.recognition_history.append(
            {
                "identity_id": identity_id,
                "name": name,
                "score": float(score or 0.0),
            }
        )
        if len(detection.recognition_history) > STABLE_RECOGNITION_WINDOW:
            detection.recognition_history = detection.recognition_history[-STABLE_RECOGNITION_WINDOW:]

        stable = _get_stable_identity(detection.recognition_history)
        should_emit_log = False

        # Nếu đã stable rồi
        if stable is not None:
            stable_key = stable["key"]
            detection.identity_id = stable["identity_id"]
            detection.type = "person"
            detection.name = stable["name"]
            detection.confidence = float(stable["score"])
            detection.is_strange = stable["name"].lower() == "unknown"
            detection.stable_identity_key = stable_key

            # Nếu trước đó chưa stable
            if previous_stable_identity_key is None:
                detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"
            # Nếu trước đó stable rồi (tức là nhận dạng nhầm -> phải sửa)
            elif stable_key != previous_stable_identity_key:
                detection.recognition_state = "corrected"
            else:
                detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"

            should_emit_log = detection.last_logged_identity_key != stable_key
            if should_emit_log:
                detection.last_logged_identity_key = stable_key
        # Nếu chưa stable, tiếp tục collect ảnh
        else:
            if detection.stable_identity_key is None:
                detection.identity_id = None
                detection.name = "unknown"
                detection.confidence = 0.0
                detection.is_strange = True
                detection.recognition_state = "collecting"
            else:
                # Nếu chưa có stable mới thì giữ stable cũ để tránh flicker.
                if detection.recognition_state == "corrected":
                    detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"

        detection.is_recognized = detection.stable_identity_key is not None
        detection.is_processing = False
        detection.last_recognized_time = time.time()
        detection.recognition_attempts += 1

        if should_emit_log:
            caption_future = executor.submit(caption_generator.get_caption, human_image)
            try:
                visual_caption = caption_future.result(timeout=CAPTION_TIMEOUT)
            except TimeoutError:
                caption_future.cancel()
                visual_caption = ""

            frame_image_path = (
                "src/modules/server/front_end/react/public/"
                f"frame_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            frame_image_name = os.path.basename(frame_image_path)
            os.makedirs("src/modules/server/front_end/react/public/", exist_ok=True)
            cv2.imwrite(frame_image_path, frame_image)

            if not detection.is_strange:
                if previous_name and previous_name.lower() != "unknown" and previous_name != detection.name:
                    title = f"False Recognition Corrected: {previous_name} -> {detection.name}"
                    system_label = (
                        "A previous stable recognition was corrected after additional evidence "
                        f"(ID={detection.identity_id}, score={detection.confidence:.3f}, votes={stable['votes']})."
                    )
                else:
                    title = f"Enter Area: {detection.name}"
                    system_label = (
                        "Recognized as a registered person in the system "
                        f"(ID={detection.identity_id}, score={detection.confidence:.3f}, votes={stable['votes']})."
                    )

                alert_service.stop_alarm_sound()
                logger.info(
                    title=title,
                    system_label=system_label,
                    file_path=frame_image_name,
                    visual_detail=visual_caption,
                )
            else:
                logger.info(
                    title="Unknown Person Detected",
                    system_label=(
                        "Identity check completed with consistent recognition results "
                        f"(Track ID={detection.tracker_id}, votes={stable['votes']})."
                    ),
                    file_path=frame_image_name,
                    visual_detail=visual_caption,
                )

        state_manager.update(detection)

    return handler
