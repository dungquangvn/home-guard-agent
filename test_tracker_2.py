import cv2

from ultralytics import YOLO
from src.modules.camera.camera import Camera

# Load the YOLO11 model
model = YOLO("models/yolo11s.pt")

# Open the video file
cam = Camera(source="data/test_vid.mp4")

# Loop through the video frames
while True:
    # Read a frame from the video
    frame_data = cam.get_frame()

    if frame_data is None:
        break
      
    if frame_data.get_id() % 10 == 1:
        # Run YOLO11 tracking on the frame, persisting tracks between frames
        results = model.track(frame_data.get_image(), persist=True)
        
        if frame_data.get_id() == 151:
            print('results[0]: ', results[0])
            print('results[0].boxes: ', results[0].boxes)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Display the annotated frame
        cv2.imshow("YOLO11 Tracking", annotated_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the video capture object and close the display window
cam.release()
cv2.destroyAllWindows()