import asyncio
import time
import cv2
from typing import List, Dict, Optional
from ultralytics import YOLO
from src.modules.camera.camera import Camera
from src.modules.alert.alert_manager import AlertManager
from src.modules.analysis.time_analyzer import TimeAnalyzer
from src.modules.logging.logger import Logger
from src.modules.recognition.face_cropper import FaceCropper
from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.recognition.plate_recognitor import PlateRecognitor
from src.core.event_bus import EventBus
from src.core.state_manager import StateManager
from src.event_handlers.on_new_person import on_new_person
from src.event_handlers.on_new_vehicle import on_new_vehicle
from src.event_handlers.on_object_left import on_object_left
from src.event_handlers.on_is_stranger import on_is_stranger
from src.event_handlers.on_stranger_over_30_seconds import on_stranger_over_30_seconds
from src.utils.classes import Detection, Person, Vehicle
        
async def main():
    cam = Camera(source="data/test_vid.mp4")  # 66.67ms/frame. source 0 là camera máy tính
    
    tracker = YOLO('models/yolo11s.pt')

    face_cropper = FaceCropper(conf=0.5)
    face_recognitor = FaceRecognitor()
    plate_recognitor = PlateRecognitor()
    alert_manager = AlertManager()
    time_analyzer = TimeAnalyzer()
    logger = Logger()
    
    state_manager = StateManager()
    event_bus = EventBus()

    # Subcribe sự kiện
    event_bus.on("new_person", on_new_person(face_cropper, face_recognitor, logger))
    event_bus.on("is_stranger", on_is_stranger(time_analyzer, logger))
    event_bus.on("new_vehicle", on_new_vehicle(plate_recognitor, logger))
    event_bus.on("object_left", on_object_left(logger))
    event_bus.on("stranger_over_30_seconds", on_stranger_over_30_seconds(alert_manager, logger))
    
    while True:
        
        frame_data = cam.get_frame()
        if frame_data is None:
            break
        if frame_data.get_id() % 5 == 1:
            results = tracker.track(frame_data.get_image(), persist=True)
            
            # Làm các thứ với results giúp phát hiện events
            # processed_results = ... results
            # events = state_manager.update(processed_results)
            
            # Bắn các events phát hiện được cho handler xử lý
            # event_bus.emit(events)
        

    # cam.release()
    
if __name__ == '__main__':
    asyncio.run(main())