import asyncio
from src.modules.recognition.face_cropper import FaceCropper
from src.modules.camera.camera import Camera
import time
import cv2

async def main():
    cam = Camera(source="data/test_vid.mp4")  # 66.67ms/frame
    cropper = FaceCropper(conf=0.5)
    start = time.time()
    count = 10
    while True:
        
        frame_data = cam.get_frame()
        if frame_data is None:
            break
        if frame_data.get_id() % 3 == 1:
            face_images_list = await cropper.crop_faces(frame_data.get_image())
        for idx, (face_img, conf) in enumerate(face_images_list):
            print(f"Face {idx}: Confidence = {conf:.2f}")
            cv2.imshow(f"Face {idx}", face_img)
        cv2.waitKey(0)
        cv2.imshow("Camera", frame_data.image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        

    cam.release()
    print(f"Duration: {time.time()-start}s.")
    
if __name__ == '__main__':
    asyncio.run(main())