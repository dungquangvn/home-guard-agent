from __future__ import annotations

from typing import Any, Dict, List

from src.modules.security_chat.rag import format_log_for_embedding, get_embeddings


class Embedder:
    def __init__(self) -> None:
        pass

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return []

        embeddings = get_embeddings(text)
        if not embeddings:
            return []

        return embeddings[0]

    def embed_log(self, log_data: Dict[str, Any]) -> List[float]:
        log_str = format_log_for_embedding(log_data)
        # print(log_str)
        return self.embed_text(log_str)


if __name__ == "__main__":
    embedder = Embedder()
    sample_log = {
        "title": "ERROR",
        "system_label": "Camera 1 phat hien chuyen dong",
        "visual_detail": "Hinh anh co nguoi di chuyen",
        "occurrence_time": "2024-06-01 12:00:00",
        "file_path": "frame_20240601_120000.jpg",
    }
    embedding = embedder.embed_log(sample_log)
    print("Embedding dim:", len(embedding))
