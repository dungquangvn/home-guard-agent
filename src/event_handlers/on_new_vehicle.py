from collections import defaultdict
import time

from src.modules.recognition.plate_recognitor import CustomLicensePlateRecognizer
from src.core.state_manager import StateManager
from src.modules.logging.logger import Logger
import os
import cv2
import datetime

STABLE_PLATE_WINDOW = 8
STABLE_PLATE_MIN_VOTES = 1
MIN_COLLECTED_IMAGES_FOR_STABLE = 3
VEHICLE_OCR_DEBUG_ENV = "VEHICLE_OCR_DEBUG"

ID_PLATE_NUMBER_MAP = {
    "201": "19s2-45678",
    "202": "19s1-37994",
    "203": "BOK5E1",
    "204": "B98E02",
}

PLATE_NUMBER_ID_MAP = {v.upper(): k for k, v in ID_PLATE_NUMBER_MAP.items()}


def _parse_bool_env(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


def _print_vehicle_ocr_debug(track_id, debug_payload):
    plates = debug_payload.get("plates", [])
    boxes = debug_payload.get("boxes", [])
    crops = debug_payload.get("crops", [])

    print(
        f"[VEHICLE_OCR_DEBUG] track_id={track_id} "
        f"detected_boxes={len(boxes)} ocr_crops={len(crops)} final_plates={plates}"
    )

    for crop_info in crops:
        idx = crop_info.get("index")
        best_text = crop_info.get("best_text")
        plate_shape = crop_info.get("plate_shape")
        processed_shape = crop_info.get("processed_shape")
        print(
            f"[VEHICLE_OCR_DEBUG] track_id={track_id} crop#{idx} "
            f"plate_shape={plate_shape} processed_shape={processed_shape} best={best_text}"
        )

        for cand in crop_info.get("candidates", []):
            raw_text = cand.get("raw_text")
            norm_text = cand.get("normalized_text")
            score = float(cand.get("score", 0.0))
            quality = float(cand.get("quality", 0.0))
            print(
                f"[VEHICLE_OCR_DEBUG] track_id={track_id} crop#{idx} "
                f"candidate raw='{raw_text}' norm='{norm_text}' score={score:.3f} quality={quality:.3f}"
            )


def _extract_plate_score(debug_payload, plate_number: str) -> float:
    """
    Get OCR confidence score for the selected plate text from debug payload.
    Prefer exact normalized_text match and use EasyOCR raw score [0..1].
    """
    target = (plate_number or "").strip().upper()
    if not target or target == "UNKNOWN":
        return 0.0

    best_score = 0.0
    for crop in debug_payload.get("crops", []):
        for cand in crop.get("candidates", []):
            cand_norm = str(cand.get("normalized_text", "")).strip().upper()
            if cand_norm == target:
                best_score = max(best_score, float(cand.get("score", 0.0) or 0.0))

    return max(0.0, min(best_score, 1.0))


def _normalize_vehicle_identity(identity_id, plate_number):
    plate_norm = (plate_number or "Unknown").strip().upper() or "Unknown"
    key_id = -1 if identity_id is None else identity_id
    return (key_id, plate_norm), key_id, plate_norm


def _get_stable_plate(history):
    """
    Nhận vào history recognition của 1 vehicle
    - Đếm số vote và tổng score cho mỗi cặp (identity_id, plate_number)
    - Trả về cặp ổn định nhất.
    """

    vote_map = defaultdict(
        lambda: {"count": 0, "score_sum": 0.0, "identity_id": None, "plate_number": "Unknown"}
    )

    for item in history:
        key, key_id, plate_norm = _normalize_vehicle_identity(
            item.get("identity_id"), item.get("plate_number")
        )
        vote_map[key]["count"] += 1
        vote_map[key]["score_sum"] += float(item.get("score", 0.0) or 0.0)
        vote_map[key]["identity_id"] = None if key_id == -1 else key_id
        vote_map[key]["plate_number"] = plate_norm

    if not vote_map:
        return None

    # Stable is allowed only after collecting at least N OCR frames.
    if len(history) < MIN_COLLECTED_IMAGES_FOR_STABLE:
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

    if best_count < STABLE_PLATE_MIN_VOTES:
        return None

    stats = vote_map[best_key]
    avg_score = stats["score_sum"] / max(stats["count"], 1)
    return {
        "key": best_key,
        "identity_id": stats["identity_id"],
        "plate_number": stats["plate_number"],
        "score": avg_score,
        "votes": stats["count"],
    }


def on_new_vehicle(
    plate_recognitor: CustomLicensePlateRecognizer,
    logger: Logger,
    state_manager: StateManager,
    debug: bool | None = None,
):
    """
    Handler cho event "new_vehicle".
    Event format:
    {
        "event": "new_vehicle",
        "data": Detection,
        "frame": FrameData
    }
    """

    debug_enabled = _parse_bool_env(os.getenv(VEHICLE_OCR_DEBUG_ENV), default=False) if debug is None else bool(debug)

    def handler(event):
        detection = event["data"]
        previous_plate_number = detection.plate_number
        previous_stable_identity_key = detection.stable_identity_key

        if detection.type == "bicycle":
            detection.identity_id = None
            detection.plate_number = "N/A"
            detection.confidence = 1.0
            detection.is_strange = False
            detection.is_recognized = True
            detection.is_processing = False
            detection.last_recognized_time = time.time()
            detection.recognition_attempts += 1

            if detection.last_logged_identity_key != ("bicycle", "N/A"):
                detection.last_logged_identity_key = ("bicycle", "N/A")
                logger.info(title="[EVENT] New Bicycle Detected")

            state_manager.update(detection)
            return

        frame_image = event["frame"].get_image()
        x, y, w, h = detection.bbox

        height, width = frame_image.shape[:2]
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(width, int(x + w))
        y2 = min(height, int(y + h))
        vehicle_crop = frame_image[y1:y2, x1:x2, :]

        debug_payload = plate_recognitor.detect_license_plates_debug(vehicle_crop)
        plates = list(debug_payload.get("plates", []))

        if debug_enabled:
            _print_vehicle_ocr_debug(detection.tracker_id, debug_payload)

        if len(plates) == 0:
            plate_number = "Unknown"
            identity_id = None
            score = 0.0
        else:
            plate_number = plates[0].upper()
            identity_id = PLATE_NUMBER_ID_MAP.get(plate_number, None)
            score = _extract_plate_score(debug_payload, plate_number)

        detection.recognition_history.append(
            {
                "identity_id": identity_id,
                "plate_number": plate_number,
                "score": float(score or 0.0),
            }
        )
        if len(detection.recognition_history) > STABLE_PLATE_WINDOW:
            detection.recognition_history = detection.recognition_history[-STABLE_PLATE_WINDOW:]

        stable = _get_stable_plate(detection.recognition_history)
        should_emit_log = False

        if stable is not None:
            stable_key = stable["key"]
            detection.identity_id = stable["identity_id"]
            detection.plate_number = stable["plate_number"]
            detection.confidence = float(stable["score"])
            detection.is_strange = (
                stable["identity_id"] is None or stable["plate_number"].lower() == "unknown"
            )
            detection.stable_identity_key = stable_key

            if previous_stable_identity_key is None:
                detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"
            elif stable_key != previous_stable_identity_key:
                detection.recognition_state = "corrected"
            else:
                detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"

            should_emit_log = detection.last_logged_identity_key != stable_key
            if should_emit_log:
                detection.last_logged_identity_key = stable_key
        else:
            if detection.stable_identity_key is None:
                detection.identity_id = None
                detection.plate_number = "Unknown"
                detection.confidence = 0.0
                detection.is_strange = True
                detection.recognition_state = "collecting"
            else:
                # Keep the old stable result until new stable evidence is formed.
                if detection.recognition_state == "corrected":
                    detection.recognition_state = "stable_unknown" if detection.is_strange else "stable_known"

        detection.is_recognized = detection.stable_identity_key is not None
        detection.is_processing = False
        detection.last_recognized_time = time.time()
        detection.recognition_attempts += 1

        if debug_enabled:
            history_snapshot = [item.get("plate_number", "Unknown") for item in detection.recognition_history]
            print(
                f"[VEHICLE_OCR_DEBUG] track_id={detection.tracker_id} "
                f"history={history_snapshot} stable={stable} state={detection.recognition_state}"
            )

        if should_emit_log:
            frame_image_path = (
                "src/modules/server/front_end/react/public/"
                f"frame_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            frame_image_name = os.path.basename(frame_image_path)
            os.makedirs("src/modules/server/front_end/react/public/", exist_ok=True)
            cv2.imwrite(frame_image_path, frame_image)

            if not detection.is_strange:
                if (
                    previous_plate_number
                    and previous_plate_number.lower() != "unknown"
                    and previous_plate_number.upper() != detection.plate_number.upper()
                ):
                    title = f"False Plate Corrected: {previous_plate_number} -> {detection.plate_number}"
                    system_label = (
                        "A previous stable plate recognition was corrected after additional evidence "
                        f"(ID={detection.identity_id}, score={detection.confidence:.3f}, votes={stable['votes']})."
                    )
                else:
                    title = f"Verified: Registered Vehicle ({detection.plate_number})"
                    system_label = (
                        "License plate recognized as a registered vehicle "
                        f"(ID={detection.identity_id}, score={detection.confidence:.3f}, votes={stable['votes']})."
                    )

                logger.info(
                    title=title,
                    system_label=system_label,
                    file_path=frame_image_name,
                    visual_detail="",
                )
            else:
                logger.info(
                    title=f"Detected: Unknown Vehicle ({detection.plate_number})",
                    system_label=(
                        "License plate recognition completed with consistent unknown result "
                        f"(Track ID={detection.tracker_id}, score={detection.confidence:.3f}, votes={stable['votes']})."
                    ),
                    file_path=frame_image_name,
                    visual_detail="",
                )

        state_manager.update(detection)

    return handler
