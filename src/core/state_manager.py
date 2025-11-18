from typing import Dict, Any, List

class StateManager:
    """
    Quản lý trạng thái của từng tracker_id để phát hiện khi:
    - 1 detection mới xuất hiện
    - 1 detection biến mất
    và lưu thông tin identity_id sau khi nhận dạng
    """
    def __init__(self, disappear_threshold: int = 1):
        self.detections: Dict[int, Dict] = {}
        self.disappear_threshold = disappear_threshold

    def update(self, tracked_detections: List[Any]):
        """
        Input: danh sách Detection sau tracker (đã có tracker_id)
        Output: list event:
            - "new_person"
            - "new_car"
            - "new_motorcycle"
            - "person_left"
            - "car_left"
            - "motorcycle_left"
        """

        events = []
        current_ids = set()

        # ----------- 1. Duyệt các detection đang xuất hiện -----------
        for det in tracked_detections:
            tracker_id = det.tracker_id
            current_ids.add(tracker_id)

            if tracker_id not in self.detections:

                # detection mới -> emit event nhận dạng
                self.detections[tracker_id] = {
                    "type": det.type,
                    "identity_id": None,
                    "recognized": False,
                    "missed": 0,
                    "data": det,
                }

                event_type = f"new_{det.type}"
                events.append({"type": event_type, "tracker_id": tracker_id, "det": det})

            else:
                # detection cũ -> reset missed counter
                self.detections[tracker_id]["missed"] = 0
                self.detections[tracker_id]["data"] = det

        # ----------- 2. Check detection biến mất -----------
        lost_ids = []
        for tracker_id in list(self.detections.keys()):
            if tracker_id not in current_ids:
                self.detections[tracker_id]["missed"] += 1

                # Mất nhiều frame → coi là detection rời khỏi khung hình
                if self.detections[tracker_id]["missed"] > self.disappear_threshold:
                    events.append({"type": f"{det.type}_left", "tracker_id": tracker_id})
                    lost_ids.append(tracker_id)

        # Xóa khỏi state
        for tracker_id in lost_ids:
            del self.detections[tracker_id]

        return events

    def set_identity(self, tracker_id: int, identity_id: int):
        """Gán identity sau khi nhận dạng"""
        if tracker_id in self.detections:
            self.detections[tracker_id]["identity_id"] = identity_id
            self.detections[tracker_id]["recognized"] = True
