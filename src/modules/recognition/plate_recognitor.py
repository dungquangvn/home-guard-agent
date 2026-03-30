import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

import re
from typing import Any, Dict, List, Optional, Tuple

import cv2
import easyocr
import numpy as np
from ultralytics import YOLO


class CustomLicensePlateRecognizer:
    def __init__(
        self,
        threshold_conf: float = 0.5,
        conf: Optional[float] = None,
        detect_model_path: str = "models/license_plate_detector_5.pt",
        device: Optional[str] = None,
    ):
        if device is None:
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"

        self.device = device
        self.conf = float(threshold_conf if conf is None else conf)
        self.detect_model = YOLO(detect_model_path).to(self.device)
        self.ocr_model = self._build_ocr_model(self.device)

        self.plates_bounding_boxes = []
        # Keep misspelled field for backward compatibility.
        self.plates_bouding_boxs = self.plates_bounding_boxes

    @staticmethod
    def _build_ocr_model(device: str):
        use_gpu = device == "cuda"
        try:
            return easyocr.Reader(["en"], gpu=use_gpu, verbose=False)
        except TypeError:
            # Compatibility for older EasyOCR versions.
            return easyocr.Reader(["en"], gpu=use_gpu)
        except Exception:
            # Fallback to CPU if GPU init fails.
            if use_gpu:
                return easyocr.Reader(["en"], gpu=False)
            raise

    @staticmethod
    def _normalize_plate_text(raw_text: str) -> str:
        text = raw_text.upper().replace(" ", "")
        text = re.sub(r"[^A-Z0-9-]", "", text)
        text = re.sub(r"-{2,}", "-", text).strip("-")
        return text[1:]

    @staticmethod
    def _candidate_quality(text: str, score: float) -> float:
        norm = CustomLicensePlateRecognizer._normalize_plate_text(text)
        bonus = 0.0
        if 5 <= len(norm) <= 12:
            bonus += 0.15
        if any(ch.isdigit() for ch in norm):
            bonus += 0.05
        if any(ch.isalpha() for ch in norm):
            bonus += 0.05
        if "-" in norm:
            bonus += 0.03
        return float(score) + bonus

    @staticmethod
    def _extract_ocr_candidates(ocr_result) -> List[Tuple[str, float]]:
        candidates: List[Tuple[str, float]] = []

        if not ocr_result:
            return candidates

        # EasyOCR result with detail=1:
        # [([x1,y1], [x2,y2], [x3,y3], [x4,y4]), text, score]
        if isinstance(ocr_result, list):
            for item in ocr_result:
                if isinstance(item, (list, tuple)):
                    if len(item) >= 3:
                        text = str(item[1])
                        score = float(item[2])
                        candidates.append((text, score))
                    elif len(item) >= 1:
                        candidates.append((str(item[0]), 1.0))
                elif isinstance(item, str):
                    candidates.append((item, 1.0))

        return candidates

    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Detect license plates in an image and return cropped plate images.
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        results = self.detect_model(image, verbose=False)
        if not results:
            return []

        detected = results[0]
        cropped_plates: List[np.ndarray] = []
        self.plates_bounding_boxes.clear()

        for box in detected.boxes:
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]

            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w))
            y2 = max(0, min(y2, h))

            self.plates_bounding_boxes.append(
                {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": conf}
            )

            if conf < self.conf:
                continue
            if x2 <= x1 or y2 <= y1:
                continue

            plate = image[y1:y2, x1:x2]
            if plate.size == 0:
                continue

            cropped_plates.append(plate.copy())

        return cropped_plates

    def process_cropped_plate_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Preprocess a cropped plate image for OCR:
        grayscale -> denoise -> threshold -> morphology.
        """
        if image is None or image.size == 0:
            return None

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        target_height = 100
        ratio = target_height / gray.shape[0]
        target_width = int(gray.shape[1] * ratio)
        
        gray = cv2.resize(gray, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
        pad = 2
        padded = cv2.copyMakeBorder(
            gray, 
            top=pad, bottom=pad, left=pad, right=pad, 
            borderType=cv2.BORDER_CONSTANT, 
            # value=[255, 255, 255] # Màu trắng
            value=[0, 0, 0]
        )
        # denoised = cv2.bilateralFilter(padded, 9, 75, 75)
        denoised = cv2.GaussianBlur(padded, (3, 3), 0) 

        # thresh = cv2.adaptiveThreshold(
        #     denoised,
        #     255,
        #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #     cv2.THRESH_BINARY,
        #     11, # original: 31. nếu ảnh sau khi morphology bị đứt nét chữ, hãy thử giảm blockSize xuống khoảng 11 hoặc 15.
        #     5, # original: 10
        # )
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        # cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

        return cleaned

    def ocr_plate_image(self, image: np.ndarray) -> Optional[str]:
        """
        Run EasyOCR on a preprocessed plate image and return the best final text.
        """
        best_text, _debug_candidates = self._ocr_plate_image_internal(image)
        return best_text

    def _ocr_plate_image_internal(self, image: np.ndarray) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Internal OCR routine that returns:
        - best_text: the final chosen plate text
        - debug_candidates: raw and normalized OCR candidates with scores
        """
        if image is None or image.size == 0:
            return None, []

        if len(image.shape) == 2:
            ocr_input = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            ocr_input = image

        try:
            ocr_result = self.ocr_model.readtext(ocr_input, detail=1, paragraph=False, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        except Exception:
            return None, []

        candidates = self._extract_ocr_candidates(ocr_result)
        if not candidates:
            return None, []

        best_text = None
        best_score = -1.0
        debug_candidates: List[Dict[str, Any]] = []

        for raw_text, score in candidates:
            norm = self._normalize_plate_text(raw_text)
            if not norm:
                continue
            quality = self._candidate_quality(norm, score)
            debug_candidates.append(
                {
                    "raw_text": str(raw_text),
                    "normalized_text": norm,
                    "score": float(score),
                    "quality": float(quality),
                }
            )
            if quality > best_score:
                best_score = quality
                best_text = norm

        return best_text, debug_candidates

    def detect_license_plates(self, image: np.ndarray) -> List[str]:
        """
        Full pipeline: detect -> preprocess -> OCR.
        Keep this method for backward compatibility with current callers.
        """
        debug_payload = self.detect_license_plates_debug(image)
        return list(debug_payload.get("plates", []))

    def detect_license_plates_debug(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Full pipeline with debug payload for each detected plate crop.
        """
        license_texts: List[str] = []
        debug_crops: List[Dict[str, Any]] = []

        cropped_plates = self.detect(image)
        for idx, plate in enumerate(cropped_plates, start=1):
            processed = self.process_cropped_plate_image(plate)
            best_text, debug_candidates = self._ocr_plate_image_internal(processed)

            debug_crops.append(
                {
                    "index": idx,
                    "best_text": best_text,
                    "plate_shape": tuple(plate.shape),
                    "processed_shape": tuple(processed.shape) if processed is not None else None,
                    "candidates": debug_candidates,
                }
            )

            if best_text:
                license_texts.append(best_text)

        # Deduplicate while preserving order.
        seen = set()
        unique_texts = []
        for txt in license_texts:
            if txt not in seen:
                unique_texts.append(txt)
                seen.add(txt)

        return {
            "plates": unique_texts,
            "boxes": list(self.plates_bounding_boxes),
            "crops": debug_crops,
        }


if __name__ == "__main__":
    TEST_IMAGE_PATH = "data/plate_number_4.png"

    recognizer = CustomLicensePlateRecognizer(threshold_conf=0.5)
    test_image = cv2.imread(TEST_IMAGE_PATH, cv2.IMREAD_COLOR)

    if test_image is None:
        raise FileNotFoundError(f"Cannot read test image: {TEST_IMAGE_PATH}")

    print("[UNIT] Running detect()")
    crops = recognizer.detect(test_image)
    assert isinstance(crops, list), "detect() must return a list"
    print(f"[UNIT] detect() -> {len(crops)} crop(s)")

    # Render detect result with bounding boxes.
    detect_vis = test_image.copy()
    for i, box in enumerate(recognizer.plates_bounding_boxes, start=1):
        x1 = int(box["x1"])
        y1 = int(box["y1"])
        x2 = int(box["x2"])
        y2 = int(box["y2"])
        conf = float(box["conf"])
        color = (0, 255, 0) if conf >= recognizer.conf else (0, 165, 255)
        cv2.rectangle(detect_vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            detect_vis,
            f"#{i} {conf:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    print("[UNIT] Running process_cropped_plate_image() + ocr_plate_image()")
    processed_previews = []
    for idx, crop in enumerate(crops):
        processed = recognizer.process_cropped_plate_image(crop)
        assert processed is not None, "Processed image must not be None"
        assert processed.size > 0, "Processed image must not be empty"

        crop_h = crop.shape[0]
        crop_w = crop.shape[1]
        processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        processed_bgr = cv2.resize(processed_bgr, (crop_w, crop_h), interpolation=cv2.INTER_NEAREST)
        preview = cv2.hconcat([crop, processed_bgr])
        cv2.putText(
            preview,
            f"Crop #{idx + 1}: left=original, right=processed",
            (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        processed_previews.append(preview)

        plate_text = recognizer.ocr_plate_image(processed)
        print(f"[UNIT] crop #{idx + 1}: OCR -> {plate_text}")

    print("[UNIT] Running full pipeline detect_license_plates()")
    plates = recognizer.detect_license_plates(test_image)
    assert isinstance(plates, list), "detect_license_plates() must return a list"
    print(f"[UNIT] Final detected plates: {plates}")

    # Render windows for manual visual verification.
    try:
        cv2.imshow("[UNIT] Detect Result", detect_vis)
        for idx, preview in enumerate(processed_previews, start=1):
            cv2.imshow(f"[UNIT] Crop Process #{idx}", preview)
        if not processed_previews:
            print("[UNIT] No cropped plates to render processing preview.")
        print("[UNIT] Press any key on image window to close previews.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error as err:
        print(f"[UNIT] OpenCV render skipped (likely headless environment): {err}")

    print("[UNIT] All tests completed.")
