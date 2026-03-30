PYTHON = python3
PYTHONPATH = .

.PHONY: help camera classes crop main cg runall

help:
	@echo "Available make targets:"
	@echo "  camera    - Run the camera module"
	@echo "  classes   - Run the types utility module"
	@echo "  crop      - Run the face cropper module"
	@echo "  runall    - Run AI pipeline + backend together"

main:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/main.py
camera:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/modules/camera/camera.py
classes:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/utils/classes.py
crop:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/modules/recognition/face_cropper.py
cg:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/modules/caption_generator/caption_generator.py
runall:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) run_all.py
