import asyncio
import time
import cv2
from typing import List, Dict, Optional
from ultralytics import YOLO
from src.modules.camera.camera import Camera
from src.modules.alerts.alerts import AlertService
from src.modules.analysis.Analysis import Analysis
from src.modules.logging.logger import Logger
from src.modules.recognition.face_cropper import FaceCropper
from src.modules.recognition.face_recognitor import FaceRecognitor
# from src.modules.recognition.plate_recognitor import PlateRecognitor
from src.modules.video_recorder.video_recorder import VideoRecorder
from src.core.event_extractor import EventExtractor
from src.core.event_bus import EventBus
from src.core.state_manager import StateManager
from src.event_handlers.on_new_person import on_new_person
# from src.event_handlers.on_new_vehicle import on_new_vehicle
# from src.event_handlers.on_object_left import on_object_left
# from src.event_handlers.on_is_stranger import on_is_stranger
# from src.event_handlers.on_stranger_over_30_seconds import on_stranger_over_30_seconds
from src.utils.classes import Detection
        
async def main():
    # cam = Camera(source="data/test_vid.mp4")
    cam = Camera(source="data/vid_1.mp4")
    video_recorder = VideoRecorder(
        fps=cam.fps,
        width=cam.width,
        height=cam.height,
    )
    
    tracker = YOLO('models/yolo11n.pt')

    # face_cropper = FaceCropper(conf=0.5)
    face_recognitor = FaceRecognitor(face_db_path='models/face_db.pkl')
    # plate_recognitor = PlateRecognitor()
    # alert_manager = AlertManager()
    # time_analyzer = TimeAnalyzer()
    logger = Logger()
    
    state_manager = StateManager()
    event_extractor = EventExtractor(state_manager)
    event_bus = EventBus()

    # Subcribe sự kiện
    event_bus.on("new_person", on_new_person(face_recognitor, logger, state_manager))
    # event_bus.on("is_stranger", on_is_stranger(time_analyzer, logger))
    # event_bus.on("new_vehicle", on_new_vehicle(plate_recognitor, logger))
    # event_bus.on("object_left", on_object_left(logger))
    # event_bus.on("stranger_over_30_seconds", on_stranger_over_30_seconds(alert_manager, logger))
    
    # start = time.time()
    
    while True:
        
        frame_data = cam.get_frame()
        if frame_data is None:
            break
        
        newest_detections = []
        
        if frame_data.get_id() % 8 == 1:
            results = tracker.track(frame_data.get_image(), persist=True)
            
            # Làm các thứ với results giúp phát hiện events
            events = event_extractor.extract(results)
            for e in events:
                e['frame'] = frame_data
            
            # Bắn các events phát hiện được cho handler xử lý
            # Trả về queue chứa kết quả của các thread module
            # chạy song song với main
            event_bus.emit(events)
                
        tracked_dets = state_manager.get_current_detections()

        for det in tracked_dets.values():
            newest_detections.append(det)
            
        for det in newest_detections:    
            frame_data.add_object(det)
            
        video_recorder.write(frame_data.image)
            
        cv2.imshow("AI-CAM", frame_data.image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    video_recorder.release()
    cam.release()
    
if __name__ == '__main__':
    asyncio.run(main())