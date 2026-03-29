import json
import os
from datetime import datetime

from flask import jsonify
from psycopg2.extras import RealDictCursor

from src.utils.postgres import get_postgres_connection

LOG_FILE_PATH = "system.log"
LOGS_FETCH_LIMIT = int(os.getenv("LOGS_FETCH_LIMIT", "500"))


def _to_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_time_string(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return _to_text(value)
    return _to_text(value)


def _normalize_log(raw_log):
    occurrence_time = _to_text(
        raw_log.get("occurrence_time")
        or raw_log.get("occurence_time")
        or raw_log.get("time")
    )
    system_label = _to_text(raw_log.get("system_label") or raw_log.get("description"))
    visual_detail = _to_text(raw_log.get("visual_detail"))
    description = _to_text(raw_log.get("description") or system_label or visual_detail)

    return {
        "id": _to_text(raw_log.get("id")),
        "title": _to_text(raw_log.get("title") or "LOG"),
        "description": description,
        "time": occurrence_time,
        "file_path": _to_text(raw_log.get("file_path")),
        "system_label": system_label,
        "visual_detail": visual_detail,
        "occurrence_time": occurrence_time,
    }


class SendLogsModules:
    def _read_logs_from_postgres(self):
        conn = get_postgres_connection(debug=False)
        if conn is None:
            return None

        rows = []
        query_sql = """
            SELECT id, title, system_label, visual_detail, occurrence_time, file_path
            FROM logs
            ORDER BY occurrence_time DESC
            LIMIT %s
        """

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query_sql, (max(1, LOGS_FETCH_LIMIT),))
                rows = cur.fetchall() or []
        except Exception as exc:
            print(f"Error loading logs from postgres: {exc}")
            return None
        finally:
            conn.close()

        normalized = []
        for row in rows:
            item = dict(row)
            item["occurrence_time"] = _to_time_string(item.get("occurrence_time"))
            normalized.append(_normalize_log(item))
        return normalized

    def _read_logs_from_file(self):
        logs = []
        if not os.path.exists(LOG_FILE_PATH):
            return logs

        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    logs.append(_normalize_log(row))
        except Exception as exc:
            print(f"Error reading or parsing log file: {exc}")
            return []

        return list(reversed(logs))

    def getLogs(self):
        postgres_logs = self._read_logs_from_postgres()
        if postgres_logs is not None:
            return jsonify(postgres_logs)

        return jsonify(self._read_logs_from_file())
