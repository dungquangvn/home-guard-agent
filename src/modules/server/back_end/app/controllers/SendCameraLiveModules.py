
import time
import cv2

class SendCameraLiveModules:
    __instance = None
    __isInitialized = False

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    #Tham số đầu vào là hàm trả về các frame của một video trực tiếp, lưu ý là hàm này không có tham số
    # và kiểu dữ liệu của frame là numpyarray(nd)
    def __init__(self, frame_provider):
        if not self.__isInitialized: 
            self._frame_provider = frame_provider
            self.__isInitialized = True

    def setFrameProvider(self, frame_provider):
        self._frame_provider = frame_provider
        
    def gen_mjpeg(self):

        while True:
            frame = self._frame_provider() if self._frame_provider else None
            if frame is None:
                time.sleep(0.01)
                continue
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = jpeg.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
   