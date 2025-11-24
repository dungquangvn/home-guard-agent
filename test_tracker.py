from ultralytics import YOLO

model = YOLO('models/yolo11s.pt')

# results = model.track(
#   'data/test_vid.mp4',
#   show=True,
# )

results = model.track(
  'https://youtu.be/JUfIpZCYquY?list=PL0XD3NW_xyMaZ6Djo5VriUJiKLORF4rc9',
  show=True,
)

for r in results:
  print(r.boxes)