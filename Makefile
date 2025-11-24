PYTHON = python3
PYTHONPATH = .

.PHONY: help camera classes crop

help:
	@echo "Available make targets:"
	@echo "  camera    - Run the camera module"
	@echo "  classes   - Run the types utility module"
	@echo "  crop      - Run the face cropper module"

camera:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/modules/camera/camera.py

classes:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/utils/classes.py


crop:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/modules/recognition/face_cropper.py
