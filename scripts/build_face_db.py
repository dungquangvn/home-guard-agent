import insightface
import cv2
import numpy as np
import os
import pickle

# Load Face Recognizer
recognizer = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
recognizer.prepare(ctx_id=-1)  # -1 = CPU

# Folder chứa ảnh người quen
base_path = "data/faces"  # ví dụ: data/faces/Binh/...

face_db = {}

# Đi qua từng folder người quen
for idx, person_name in enumerate(os.listdir(base_path)):
    person_folder = os.path.join(base_path, person_name)
    if not os.path.isdir(person_folder):
        continue

    embeddings = []

    for img_name in os.listdir(person_folder):
        if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        img_path = os.path.join(person_folder, img_name)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Không đọc được ảnh: {img_path}")
            continue

        faces = recognizer.get(img)
        if len(faces) == 0:
            print(f"Không tìm thấy mặt: {img_path}")
            continue

        # lấy face đầu tiên nếu nhiều mặt
        face = faces[0]
        embeddings.append(face.normed_embedding)

    # Tính embedding trung bình và normalize
    if embeddings:
        avg_emb = np.mean(embeddings, axis=0)
        avg_emb /= np.linalg.norm(avg_emb)  # normalize

        # Lưu cả id và embedding
        face_db[idx] = {
            "id": 1000 + idx,
            "name": person_name,
            "embedding": avg_emb
        }
        print(f"Đã lưu embedding cho: {person_name} (id={1000 + idx})")

# Lưu database ra file bằng pickle
with open("models/face_db.pkl", "wb") as f:
    pickle.dump(face_db, f)

print("Hoàn tất! Database lưu vào models/face_db.pkl")