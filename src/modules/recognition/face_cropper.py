from typing import List, Tuple
import cv2
import numpy as np
from src.utils.classes import FrameData
from ultralytics import YOLO
import time
import asyncio
        
class FaceCropper:
    def __init__(self, model_path='models/yolov12n-face.pt', conf=0.5):
        self.detector = YOLO(model_path)
        self.conf = conf
        
    async def _detect(self, image: np.ndarray):
        results = self.detector.predict(image)
        
        faces_list = []
        for r in results:
            bbox_list = r.boxes.xyxy.cpu().numpy()
            conf_score_list = r.boxes.conf.cpu().numpy()
            for bbox, conf in zip(bbox_list, conf_score_list):
                if conf >= self.conf:
                    x1, y1, x2, y2 = map(int, bbox)
                    faces_list.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': conf
                    })
            
        return faces_list

    async def crop_faces(self, image: np.ndarray) -> List[Tuple[np.ndarray, float]]:
        faces_list = await self._detect(image)
        face_images_list = []
        for face_dict in faces_list:
            x1, y1, x2, y2 = face_dict['bbox']
            conf = face_dict['confidence']
            face_img = image[y1:y2, x1:x2]
            face_images_list.append({
                "face_image": face_img,
                "confidence": conf
            })
        return face_images_list
      
async def main():
    # Test FaceCropper
    cropper = FaceCropper(conf=0.5)
    image = cv2.imread("data/test_img.jpg", cv2.IMREAD_COLOR)
    # cv2.imshow("Input Image", image)
    # cv2.waitKey(0)

    start = time.time()
    face_images_list = await cropper.crop_faces(image)
    print(f"Duration: {time.time()-start}ms.")
    for idx, face_img_dict in enumerate(face_images_list):
        face_img = face_img_dict.get("face_image")
        conf = face_img_dict.get("confidence")
        print(f"Face {idx}: Confidence = {conf:.2f}")
        cv2.imshow(f"Face {idx}", face_img)
        cv2.waitKey(0)

    cv2.destroyAllWindows()
    
if __name__ == '__main__':
    asyncio.run(main())