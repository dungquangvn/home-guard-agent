import re
import cv2
import easyocr
from ultralytics import YOLO

class LicensePlateRecognizer:
    __instance = None
    __isInitialized = False

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    # Tham số khởi tạo là ngưỡng tin cậy để nhận diện một object là biển số
    def __init__(self, threshold_conf):
        if not self.__isInitialized : 
            self.reader = easyocr.Reader(['en'], gpu=False)
            self.__isInitialized = True
            self.detect_model = YOLO('models/license_plate_detector.pt')
            self.conf = threshold_conf
            
            


    #Hàm nhận diện biển số xe: đầu vào là ảnh, đầu ra là chuỗi biển số xe (string)
    def detect_license_plates(self, image):
        
        h, w, _ = image.shape

        results = self.detect_model(image)
        
        license_plates_detected = results[0]

        license_texts = []

        for box in license_plates_detected.boxes: 
            x1, y1, x2, y2 = box.xyxy[0]  
            conf = box.conf[0]  
            
            print(f"check confident of object: {conf} " )

            if conf >= self.conf:
                 # Crop vùng biển số
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                plate = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                if plate.size == 0:
                    continue

                # OCR nhận diện chữ trên biển số
                plate_rgb = cv2.cvtColor(plate, cv2.COLOR_BGR2RGB)
                ocr_result = self.reader.readtext(plate_rgb)

                # Ghép các ký tự thành chuỗi
                text = " ".join([res[1] for res in ocr_result]).strip()
                if text:
                    text = re.sub(r'[^A-Za-z0-9.\- ]+', '', text)
                    license_texts.append(text)

        return license_texts
        
if __name__ == "__main__":
    recognizer = LicensePlateRecognizer(threshold_conf=0.5)
    test_image = cv2.imread("data/plate_number_3.png", cv2.IMREAD_COLOR)
    cv2.imshow("Test Image", test_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    plates = recognizer.detect_license_plates(test_image)
    print("Detected License Plates:", plates)
