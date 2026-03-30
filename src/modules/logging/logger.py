import os
import threading
from datetime import datetime
import uuid
import json

from src.modules.logging.log_embedder import Embedder
from src.utils.postgres import insert_rows, get_postgres_connection


class Logger:
    def __init__(self):
        self.embedder = Embedder()
        # self.pg_table = "logs"
        self.pg_table = "mock_logs"
        self.conn = get_postgres_connection(debug=True)
        self.file_lock = threading.Lock()
        self.debug_json_log_path = os.environ.get("DEBUG_JSON_LOG_PATH", "data/debug_logs.jsonl")
        debug_log_dir = os.path.dirname(self.debug_json_log_path)
        if debug_log_dir:
            os.makedirs(debug_log_dir, exist_ok=True)

        self.log_metadata = {
            "info": {"title": "INFO", "description": "General Information"},
            "warning": {"title": "WARNING", "description": "System Warning"},
            "error": {"title": "ERROR", "description": "Application Error"},
            "debug": {"title": "DEBUG", "description": "Debugging Message"},
        }

    def _write_debug_json(self, entry):
        try:
            with self.file_lock:
                with open(self.debug_json_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Failed to write debug JSON log: {e}")

    def _write(self, level, system_label=None, custom_title=None, file_path=None, visual_detail=None):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        metadata = self.log_metadata.get(level.lower(), {"title": level.upper(), "description": "Custom Event"})

        log_data_entry = {
            "id": str(uuid.uuid4()),
            "title": custom_title if custom_title else metadata["title"],
            "system_label": system_label if system_label else "",
            "visual_detail": visual_detail if visual_detail else "",
            "occurrence_time": timestamp,
            "file_path": file_path if file_path else "",
        }
        self._write_debug_json(log_data_entry)

        # Insert log data into PostgreSQL with embedding
        try:
            # print('Generating Embedding...')
            embedding = self.embedder.embed_log(log_data_entry)
            # print('Embeded Successfully.')
            db_entry = {**log_data_entry, "embedding": embedding}
            # print('db entry:', db_entry)
            insert_rows(
                table_name=self.pg_table,
                data={k: [v] for k, v in db_entry.items()},
                conn=self.conn,
                debug=False,
            )
            print('Inserted Successfully.')
        except Exception as e:
            # Avoid breaking logging if embedding or DB insert fails
            print(f"Failed to insert log into DB: {e}. entry={log_data_entry}")

    def info(self, title, system_label=None, file_path=None, visual_detail=None):
        self._write("info", system_label, custom_title=title, file_path=file_path, visual_detail=visual_detail)

    def warning(self, title, system_label=None, file_path=None, visual_detail=None):
        self._write("warning", system_label, custom_title=title, file_path=file_path, visual_detail=visual_detail)

    def error(self, title, system_label=None, file_path=None, visual_detail=None):
        self._write("error", system_label, custom_title=title, file_path=file_path, visual_detail=visual_detail)

    def debug(self, title, system_label=None, file_path=None, visual_detail=None):
        self._write("debug", system_label, custom_title=title, file_path=file_path, visual_detail=visual_detail)


if __name__ == "__main__":
    logger = Logger()
    logger.info(
        title="Unknown Person Detected: Track ID=11",
        system_label="Unrecognized individual entered the monitored area (Track ID=11).",
        visual_detail="Person wearing dark hoodie, long pants, face partially obscured.",
        occurrence_time="2026-03-02 00:12:08"
    )
