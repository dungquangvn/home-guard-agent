from __future__ import annotations

import json
from datetime import datetime
import re
from typing import Any, Iterable, Iterator, Mapping

import numpy as np
import ollama
from psycopg2.extras import RealDictCursor

from src.utils.postgres import get_postgres_connection

# EMBEDDING_MODEL = "qwen3-embedding:0.6b"
EMBEDDING_MODEL = "embeddinggemma:300m-qat-q4_0"
# GENERATION_MODEL = "qwen3:0.6b"
GENERATION_MODEL = "lfm2.5-thinking:1.2b-q4_K_M"
RETRIEVAL_INSTRUCTION = (
    "Retrieve relevant security logs within the specified time range. Preserve "
    "chronological order to capture event flow and include any corrected or "
    "updated logs. Include logs related to unusual situations such as night "
    "activity or multiple unknown persons without any registered person. "
    "Also include cases where unknown persons appear with registered persons "
    "(possible guests), and logs containing distinguishing traits (e.g., glasses, hats)."
)

AUGMENT_INSTRUCTION = (
    "Use ACTUAL names for registered/verified persons (from log titles, after the ':'). "
    "'Unknown person' may be a stranger or unverified familiar individual. "
    "Each 'detected' or 'left area' log refers to one person. "
    "Maintain chronological order and interpret titles as events. "
    f"Current time: {datetime.now()}. "
    "Summarize each person in one sentence with appearance and departure times. "
    "Night activity or multiple unknown persons without any registered person is unusual. "
    "Unknown persons with registered persons may be guests. "
    "For unknown persons, note distinguishing traits (e.g., glasses, hats)."
)

MAX_LOGS_FOR_RAG = 800


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _strip_think_block(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    return cleaned.strip()


def normalize_log_record(raw_log: Mapping[str, Any]) -> dict[str, str]:
    occurrence_time = _safe_text(
        raw_log.get("occurrence_time")
        or raw_log.get("occurence_time")
        or raw_log.get("time")
    )
    system_label = _safe_text(raw_log.get("system_label") or raw_log.get("description"))
    visual_detail = _safe_text(raw_log.get("visual_detail"))
    description = _safe_text(raw_log.get("description") or system_label or visual_detail)

    return {
        "id": _safe_text(raw_log.get("id")),
        "title": _safe_text(raw_log.get("title") or "LOG"),
        "description": description,
        "time": occurrence_time,
        "file_path": _safe_text(raw_log.get("file_path")),
        "system_label": system_label,
        "visual_detail": visual_detail,
        "occurrence_time": occurrence_time,
    }


def _to_jsonable_time(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return _safe_text(value)
    return _safe_text(value)


def _normalize_embedding(value: Any) -> list[float]:
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        try:
            return [float(v) for v in value]
        except (TypeError, ValueError):
            return []

    text = _safe_text(value)
    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [float(v) for v in parsed]
        except (json.JSONDecodeError, TypeError, ValueError):
            raw_items = text[1:-1].split(",")
            cleaned: list[float] = []
            for item in raw_items:
                item = item.strip()
                if not item:
                    continue
                try:
                    cleaned.append(float(item))
                except ValueError:
                    return []
            return cleaned

    return []


def _parse_occurrence_time(text: str) -> datetime:
    clean_text = _safe_text(text)
    if not clean_text:
        return datetime.min

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(clean_text, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(clean_text)
    except ValueError:
        return datetime.min


def load_logs_for_rag(
    limit: int = MAX_LOGS_FOR_RAG,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    conn = get_postgres_connection(debug=False)
    if conn is None:
        return []

    safe_limit = max(1, int(limit)) if limit else MAX_LOGS_FOR_RAG

    where_clauses: list[str] = []
    query_params: list[Any] = []

    if _safe_text(start_time):
        where_clauses.append("occurrence_time >= %s")
        query_params.append(_safe_text(start_time))

    if _safe_text(end_time):
        where_clauses.append("occurrence_time <= %s")
        query_params.append(_safe_text(end_time))

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query_params.append(safe_limit)

    query_sql = f"""
        SELECT id, title, system_label, visual_detail, occurrence_time, file_path, embedding
        FROM logs
        {where_sql}
        ORDER BY occurrence_time DESC
        LIMIT %s
    """

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query_sql, tuple(query_params))
            rows = cur.fetchall() or []
    except Exception:
        return []
    finally:
        conn.close()

    normalized_logs: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        record["occurrence_time"] = _to_jsonable_time(record.get("occurrence_time"))
        log_data = normalize_log_record(record)
        log_data["embedding"] = _normalize_embedding(record.get("embedding"))
        normalized_logs.append(log_data)

    return normalized_logs


def format_log_for_embedding(log_data: Mapping[str, Any]) -> str:
    system_label = str(log_data.get("system_label", "")).strip()
    visual_detail = str(log_data.get("visual_detail", "none")).strip()
    occurrence_time = str(
        log_data.get("occurrence_time", log_data.get("occurence_time", ""))
    ).strip()
    title = str(log_data.get("title", "")).strip()

    return (
        f"Title: {title}. "
        f"System label: {system_label}. Visual detail: {visual_detail}. "
        f"Occurrence time: {occurrence_time}. "
    )


def _normalize_docs_input(docs: Iterable[str] | str) -> list[str]:
    if isinstance(docs, str):
        docs = [docs]

    normalized_docs = [str(doc).strip() for doc in docs if str(doc).strip()]
    if not normalized_docs:
        return []
    return normalized_docs


def _get_embeds_from_response(resp: Any) -> list[list[float]]:
    if isinstance(resp, Mapping):
        embeddings = resp.get("embeddings", [])
    else:
        embeddings = getattr(resp, "embeddings", [])
    return [list(map(float, emb)) for emb in embeddings]


def get_embeddings(docs: Iterable[str] | str, model: str = EMBEDDING_MODEL) -> list[list[float]]:
    normalized_docs = _normalize_docs_input(docs)
    if not normalized_docs:
        return []

    resp = ollama.embed(
        model=model,
        input=normalized_docs,
    )
    return _get_embeds_from_response(resp)


def retrieve_docs(
    user_query: str,
    all_docs: list[str],
    all_docs_embeddings: list[list[float]],
    top_k: int = 6,
) -> list[str]:
    if top_k <= 0:
        return []
    if not user_query.strip() or not all_docs:
        return []

    usable_count = min(len(all_docs), len(all_docs_embeddings))
    if usable_count == 0:
        return []

    docs = all_docs[:usable_count]
    docs_embeddings = all_docs_embeddings[:usable_count]
    query_text = f"{RETRIEVAL_INSTRUCTION}\nQuery: {user_query.strip()}"
    query_embeddings = get_embeddings(query_text)
    if not query_embeddings:
        return []

    query_vector = np.asarray(query_embeddings[0], dtype=np.float32)
    docs_matrix = np.asarray(docs_embeddings, dtype=np.float32)

    if docs_matrix.ndim == 1:
        docs_matrix = docs_matrix.reshape(1, -1)

    if docs_matrix.shape[1] != query_vector.shape[0]:
        return []

    docs_norm = np.linalg.norm(docs_matrix, axis=1)
    query_norm = np.linalg.norm(query_vector)
    denom = (docs_norm * query_norm) + 1e-12
    scores = (docs_matrix @ query_vector) / denom

    k = min(top_k, len(docs))
    top_indices = np.argsort(scores)[-k:][::-1]
    return [docs[idx] for idx in top_indices]


def retrieve_doc_indices(
    user_query: str,
    all_docs: list[str],
    all_docs_embeddings: list[list[float]],
    top_k: int = 6,
) -> list[int]:
    if top_k <= 0:
        return []
    if not user_query.strip() or not all_docs:
        return []

    usable_count = min(len(all_docs), len(all_docs_embeddings))
    if usable_count == 0:
        return []

    docs_embeddings = all_docs_embeddings[:usable_count]
    query_text = f"{RETRIEVAL_INSTRUCTION}\nQuery: {user_query.strip()}"
    query_embeddings = get_embeddings(query_text)
    if not query_embeddings:
        return []

    query_vector = np.asarray(query_embeddings[0], dtype=np.float32)
    docs_matrix = np.asarray(docs_embeddings, dtype=np.float32)

    if docs_matrix.ndim == 1:
        docs_matrix = docs_matrix.reshape(1, -1)

    if docs_matrix.shape[1] != query_vector.shape[0]:
        return []

    docs_norm = np.linalg.norm(docs_matrix, axis=1)
    query_norm = np.linalg.norm(query_vector)
    denom = (docs_norm * query_norm) + 1e-12
    scores = (docs_matrix @ query_vector) / denom

    k = min(top_k, usable_count)
    top_indices = np.argsort(scores)[-k:][::-1]
    return [int(idx) for idx in top_indices]


def build_rag_prompt(user_query: str, relevant_docs: list[str]) -> str:
    context = "\n".join(
        f"[Log #{idx}] {doc}" for idx, doc in enumerate(relevant_docs, start=1)
    )
    if not context:
        context = "[No relevant logs found]"

    return (
        "You are an AI home-security assistant. Use the information captured by the security camera in the form of logs to answer user questions.\n\n"
        f"Instruction:\n{AUGMENT_INSTRUCTION}\n\n"
        f"User question:\n{user_query.strip()}\n\n"
        f"Relevant logs:\n{context}\n\n"
        "If evidence is missing in logs, state that clearly."
    )


def augment_answer(
    user_query: str,
    relevant_docs: list[str],
    model: str = GENERATION_MODEL,
    stream: bool = False,
) -> str | Iterator[str]:
    prompt = build_rag_prompt(user_query=user_query, relevant_docs=relevant_docs)
    resp = ollama.generate(
        model=model,
        prompt=prompt,
        stream=stream,
    )

    if not stream:
        if isinstance(resp, Mapping):
            return _strip_think_block(str(resp.get("response", "")))
        return _strip_think_block(str(getattr(resp, "response", "")))

    def _stream_tokens() -> Iterator[str]:
        for chunk in resp:
            if isinstance(chunk, Mapping):
                token = str(chunk.get("response", ""))
            else:
                token = str(getattr(chunk, "response", ""))
            if token:
                yield token

    return _stream_tokens()


def answer_log_query(
    user_query: str,
    top_k: int = 6,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    query = user_query.strip()
    if not query:
        return {
            "question": "",
            "answer": "Vui lòng nhập câu hỏi trước khi truy vấn.",
            "retrieved_logs": [],
        }

    logs = load_logs_for_rag(
        limit=MAX_LOGS_FOR_RAG,
        start_time=start_time,
        end_time=end_time,
    )
    if not logs:
        return {
            "question": query,
            "answer": "Không tìm thấy dữ liệu log để truy vấn.",
            "retrieved_logs": [],
        }

    docs = [format_log_for_embedding(log) for log in logs]

    try:
        doc_embeddings: list[list[float]] = []
        missing_embedding_doc_indices: list[int] = []

        for idx, log in enumerate(logs):
            emb = log.get("embedding", [])
            if isinstance(emb, list) and emb:
                doc_embeddings.append([float(v) for v in emb])
            else:
                doc_embeddings.append([])
                missing_embedding_doc_indices.append(idx)

        if missing_embedding_doc_indices:
            docs_missing_embeddings = [docs[idx] for idx in missing_embedding_doc_indices]
            generated_embeddings = get_embeddings(docs_missing_embeddings)
            if len(generated_embeddings) == len(docs_missing_embeddings):
                for idx, generated_emb in zip(missing_embedding_doc_indices, generated_embeddings):
                    doc_embeddings[idx] = generated_emb
            else:
                doc_embeddings = get_embeddings(docs)

        if not doc_embeddings or any(not emb for emb in doc_embeddings):
            doc_embeddings = get_embeddings(docs)

        embedding_dims = {len(emb) for emb in doc_embeddings if emb}
        if len(embedding_dims) > 1:
            doc_embeddings = get_embeddings(docs)

        indices = retrieve_doc_indices(
            user_query=query,
            all_docs=docs,
            all_docs_embeddings=doc_embeddings,
            top_k=top_k,
        )
        if not indices:
            return {
                "question": query,
                "answer": "Không truy xuất được log phù hợp với câu hỏi.",
                "retrieved_logs": [],
            }

        retrieved_pairs = [
            (logs[idx], docs[idx])
            for idx in indices
            if 0 <= idx < len(logs) and 0 <= idx < len(docs)
        ]
        retrieved_pairs.sort(
            key=lambda pair: _parse_occurrence_time(pair[0].get("occurrence_time", ""))
        )

        retrieved_logs = [pair[0] for pair in retrieved_pairs]
        retrieved_docs = [pair[1] for pair in retrieved_pairs]

        answer = augment_answer(user_query=query, relevant_docs=retrieved_docs)
        return {
            "question": query,
            "answer": str(answer).strip() or "Không tạo được câu trả lời từ ngữ cảnh hiện có.",
            "retrieved_logs": retrieved_logs,
        }
    except Exception as exc:
        return {
            "question": query,
            "answer": "Không thể xử lý truy vấn RAG ở thời điểm này.",
            "retrieved_logs": [],
            "error": str(exc),
        }


if __name__ == "__main__":
    print("==== EMBEDDING TEST ====")
    sample_docs = ["Hi this is a sentence to test embedding."]
    embeddings = get_embeddings(sample_docs)
    print("Docs:", len(sample_docs))
    print("Embeddings:", len(embeddings))
    if embeddings:
        print("Embedding dim:", len(embeddings[0]))
