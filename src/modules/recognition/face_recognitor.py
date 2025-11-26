from typing import List
import numpy as np
import pickle
import insightface
from numpy.linalg import norm
import onnxruntime as ort
from typing import Dict, List

def get_available_provider():
    provider = ort.get_available_providers()
    if 'CUDAExecutionProvider' in provider:
        return ["CUDAExecutionProvider"]
    return ["CPUExecutionProvider"]

class FaceRecognitor:
    def __init__(self, face_db_path: str = "face_db.pkl", sim_threshold: float = 0.32):
        """
        face_db_path: file pickle chứa {name: embedding}
        sim_threshold: ngưỡng cosine similarity để nhận diện quen/lạ
        """
        # Load database
        with open(face_db_path, "rb") as f:
            self.face_db = pickle.load(f)
        
        # Threshold
        self.sim_threshold = sim_threshold

        # Load InsightFace model
        provider = get_available_provider()
        
        self.recognizer = insightface.app.FaceAnalysis(
            name='buffalo_l',
            providers=provider
        )
        self.recognizer.prepare(ctx_id=0 if "CUDAExecutionProvider" in provider else -1)  # CPU

    # Cosine similarity
    @staticmethod
    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (norm(a) * norm(b))

    # Nhận diện danh tính từ crops
    def recognize_faces(self, crops: List[np.ndarray]) -> List[Dict]:
        """
        crops: list các ảnh đã crop từ YOLO
        return: list các dict dạng
        {
            'identity_id': x,
            'name': y
        }
        """
        labels = []
        for crop in crops:
            faces = self.recognizer.get(crop)
            if len(faces) == 0:
                labels.append({
                    'identity_id': None,
                    'name': "Unknown",
                    'score': 0.0
                })
                continue

            # Embedding mặt
            face_emb = faces[0].normed_embedding
            face_emb /= norm(face_emb)

            # So sánh với database
            best_sim = 0
            best_identity_id = None
            best_name = "Unknown"

            for idx, db_entry in self.face_db.items():
                db_emb = db_entry["embedding"]
                sim = self.cosine_sim(face_emb, db_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_identity_id = db_entry["id"]
                    best_name = db_entry["name"]

            if best_sim >= self.sim_threshold:
                labels.append({
                    'identity_id': best_identity_id,
                    'name': best_name,
                    'score': best_sim
                })
            else:
                labels.append({
                    'identity_id': None,
                    'name': "Unknown",
                    'score': 0.0
                })
        return labels

    @staticmethod
    def draw_labels(frame: np.ndarray, detections: List[tuple], labels: List[str]):
        """
        detections: list (x1, y1, x2, y2, conf) từ YOLO
        labels: list tên nhận diện
        """
        import cv2
        for (x1, y1, x2, y2, conf), label in zip(detections, labels):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame, label, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        return frame

if __name__ == "__main__":
    import cv2

    # Load Face DB
    embedder = FaceRecognitor("models/face_db.pkl")

    # read 1 crop
    crop = cv2.imread("data/test_img.jpg")
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

    labels = embedder.recognize_faces([crop_rgb])
    print("Result:", labels)


