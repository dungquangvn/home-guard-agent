async on_new_person(face_cropper, face_recognitor, state):
    async def handler(event):
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