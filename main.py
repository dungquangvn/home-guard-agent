import asyncio
import time
import cv2
from typing import List, Dict, Optional
from src.modules.camera.camera import Camera
from src.modules.detection.object_detector import ObjectDetector
from modules.tracking.object_tracker import ObjectTracker
from src.modules.recognition.face_cropper import FaceCropper
from src.modules.recognition.face_recognitor import FaceRecognitor
from src.modules.recognition.plate_recognitor import PlateRecognitor
from src.core.event_bus import EventBus
from src.core.state_manager import StateManager

from src.utils.classes import Detection, Person, Vehicle

FAMILIAR_PLATE_NUMBER_DICT = {
    '201': '19s2-45678',
    '202': '19s1-37994'
}

async on_new_person(face_cropper, face_recognitor, state):
    async def handler(event):
        
async def main():
    cam = Camera(source="data/test_vid.mp4")  # 66.67ms/frame
    
    object_detector = ObjectDetector()
    object_tracker = ObjectTracker()
    face_cropper = FaceCropper(conf=0.5)
    face_recognitor = FaceRecognitor()
    plate_recognitor = PlateRecognitor()
    
    state_manager = StateManager()
    event_bus = EventBus()

    # Subcribe sự kiện
    event_bus.on("new_person", on_new_person(face_cropper, face_recognitor))
    event_bus.on("new_car", on_new_car(plate_recognitor))
    event_bus.on("new_motorcycle", on_new_motorcycle(plate_recognitor))
    event_bus.on("person_left", ...)
    
    
    start = time.time()
    
    while True:
        
        frame_data = cam.get_frame()
        if frame_data is None:
            break
        if frame_data.get_id() % 5 == 1:
            detections: List[Detection] = object_detector.detect(frame_data)
            tracked_detections = object_tracker.update(detections)                # gán id tracking
            for detection in detections:
                # Crop ảnh theo bbox detection
                x, y, w, h = detection.bbox
                frame_img = frame_data.get_image()
                img = frame_img[y:y+h, x:x+w]
                if detection.type == 'person':
                    # Cố gắng crop mặt
                    face_images_list: List[Dict] = await face_cropper.crop_faces(img)
                    
                    person_data = {
                        'id': 999,
                        'name': 'unknown',
                        'confidence': 0.5,
                        'is_strange': True
                    }
                    # Nếu k thấy mặt
                    if len(face_images_list) == 0:
                        # Dùng thân người
                        pass
                    
                    # Nếu có mặt -> lấy mặt đầu
                    face_image = face_images_list[0].get('face_image')
                    
                    person_id, name, confidence, is_strange, _ = face_recognitor.recognize(face_image)
                    
                    person = Person(
                        bbox=detection.bbox,
                        name=name,
                        id=person_id,
                        confidence=confidence,
                        is_strange=is_strange
                    )
                    
                    frame_data.add_object(person)
                
                elif detection.type in ['car', 'motorcycle']:
                    plate_number_list: List[Dict] = plate_recognitor.recognize(img)
                    if len(plate_number_list) == 0:
                        # skip
                        pass
                    plate_number = plate_number_list[0].get('plate_number')
                    for (id, familiar_plate_number) in FAMILIAR_PLATE_NUMBER_DICT.items():
                        if familiar_plate_number == plate_number:
                            vehicle = Vehicle(
                                vehicle_type=detection.type,
                                plate_number=plate_number,
                                id=id,
                                is_strange=False,
                                confidence=plate_number_list[0].get('confidence')
                            )
                            frame_data.add_object(vehicle)
                        else:
                            vehicle = Vehicle(
                                vehicle_type=detection.type,
                                plate_number=plate_number,
                                id=-200 - detection.tracker_id,            # gán id unknown
                                is_strange=True,
                                confidence=0.5
                            )
                            frame_data.add_object(vehicle)
                    
                    
                    
        # for idx, (face_img, conf) in enumerate(face_images_list):
            # print(f"Face {idx}: Confidence = {conf:.2f}")
            # cv2.imshow(f"Face {idx}", face_img)
        #     cv2.waitKey(0)
        # cv2.imshow("Camera", frame_data.image)
        
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        

    # cam.release()
    print(f"Duration: {time.time()-start}s.")
    
if __name__ == '__main__':
    asyncio.run(main())