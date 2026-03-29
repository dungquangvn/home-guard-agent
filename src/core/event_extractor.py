from src.utils.classes import Detection
from typing import List, Dict

class EventExtractor:

    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.TYPE_DICT = {
            'person': 0,
            'bicycle': 1,
            'car': 2,
            'motorcycle': 3
        }

    def extract(self, results) -> List[Dict]:
        """Trả về list các events dạng:
        [{"event": "new_person", "data": {...}}, ...]
        """
        events = []
        current_ids = []
        boxes = results[0].boxes

        if boxes is None:
            return self.state_manager.detect_left_objects(current_ids)

        for i in range(len(boxes)):
            object_type_id = int(boxes.cls[i])

            # chỉ quan tâm person, xe
            object_type = None
            for cls, cls_id in self.TYPE_DICT.items():
                if cls_id == object_type_id:
                    object_type = cls
                    break
            
            if object_type is None:
                continue

            # tọa độ
            x_center, y_center, w, h = boxes.xywh[i].cpu().numpy()
            x = x_center - w / 2
            y = y_center - h / 2
            track_id = int(boxes.id[i]) if boxes.id is not None else None
            if track_id is None:
                # Skip untracked detections to avoid unstable state/object_left noise.
                continue

            current_ids.append(track_id)
            conf = float(boxes.conf[i])
  
            obj = Detection(
                bbox=(x, y, w, h),
                tracker_id=track_id,
                type=object_type,
                confidence=conf
            )

            # dùng state_manager để cập nhật trạng thái cho từng object detect được
            events.extend(self.state_manager.update_object(obj))
        
        # Phát hiện các object đã rời đi
        events += self.state_manager.detect_left_objects(current_ids)

        return events
