import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import re
import cv2
from fast_plate_ocr import LicensePlateRecognizer
import matplotlib.pyplot as plt
from ultralytics import YOLO
import easyocr

class CustomLicensePlateRecognizer:
    __instance = None
    __isInitialized = False

    plates_bouding_boxs = []
    

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    # Tham số khởi tạo là ngưỡng tin cậy để nhận diện một object là biển số
    def __init__(self, threshold_conf):
        if not self.__isInitialized : 
            self.ocr = LicensePlateRecognizer("cct-s-v1-global-model", device='cuda')
            # self.ocr = easyocr.Reader(['en'], gpu=True)
            self.__isInitialized = True
            self.detect_model = YOLO('models/license_plate_detector_5.pt').to('cuda')
            self.conf = threshold_conf
            
    def __postProcessing(self, detected_lp) -> str:
        # EasyOCR trả về text thô, bạn có thể lọc chỉ giữ chữ và số ở đây
        return detected_lp.strip().upper()
    
    def __preProcessing(self, img):
        pass


    # Hàm nhận diện biển số xe: đầu vào là ảnh, đầu ra là chuỗi biển số xe (string)
    def detect_license_plates(self, image):
        
        h, w, _ = image.shape

        results = self.detect_model(image)
        
        license_plates_detected = results[0]

        license_texts = []

        for box in license_plates_detected.boxes: 
            x1, y1, x2, y2 = box.xyxy[0]  
            conf = box.conf[0]  
            
            print(f"Found licencse plate bbox, conf={conf} " )

            self.plates_bouding_boxs.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

            if conf >= self.conf:
                 # Crop vùng biển số
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                cv2.rectangle(image, (x1, y1), (x2, y2), (0,255,0), 2)

                plate = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                if plate.size == 0:
                    continue

                # OCR nhận diện chữ trên biển số
                plate_rgb = cv2.cvtColor(plate, cv2.COLOR_BGR2RGB)
                ocr_result = self.ocr.run(plate_rgb)
                # ocr_results = self.ocr.readtext(plate_rgb, detail=0) 
                
                if ocr_result and len(ocr_result) > 0:
                    final_text = self.__postProcessing(ocr_result[0])
                    if final_text:
                        license_texts.append(final_text)
                        
                # if ocr_results:
                #     # Nối các phần văn bản lại (ví dụ biển 2 dòng)
                #     combined_text = "".join(ocr_results)
                #     final_text = self.__postProcessing(combined_text)
                #     license_texts.append(final_text)
                # else:
                #     print("OCR unable to recognize plate number")

        return license_texts

        
if __name__ == "__main__":

    recognizer = CustomLicensePlateRecognizer(threshold_conf=0.5)
    print(f"YOLO Version: {recognizer.detect_model.ckpt['model'].yaml['backbone']}")
    # test_image = cv2.imread("data/plate_number_4.png", cv2.IMREAD_COLOR)
    # h,w, _ = test_image.shape
    # plates = recognizer.detect_license_plates(test_image)
    # cv2.imshow("Test Image", test_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # print("Detected License Plates:", plates)

