import uuid

from src.modules.logging.log_embedder import Embedder
from src.utils.postgres import get_postgres_connection, insert_rows


MOCK_LOGS = [
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=11, votes=3).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing long-sleeve top, trousers, carrying backpack.",
        "occurrence_time": "2026-03-02 00:12:08",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=12, votes=3).",
        "visual_detail": "A woman aged 18-60, viewed from the front, wearing short-sleeve top, trousers, wearing glasses.",
        "occurrence_time": "2026-03-02 00:12:11",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=13, votes=4).",
        "visual_detail": "A man aged 18-60, viewed from the side, wearing long coat, trousers, carrying backpack, wearing hat.",
        "occurrence_time": "2026-03-02 00:12:15",
    },
    {
        "title": "Alert: Unknown Person Staying Too Long",
        "system_label": "An unknown person is staying in the monitored area without any known person present (Track ID=11).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing long-sleeve top, trousers, carrying backpack.",
        "occurrence_time": "2026-03-02 00:27:08",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=11).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing long-sleeve top, trousers, carrying backpack.",
        "occurrence_time": "2026-03-02 00:27:59",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=12).",
        "visual_detail": "A woman aged 18-60, viewed from the front, wearing short-sleeve top, trousers, wearing glasses.",
        "occurrence_time": "2026-03-02 00:28:02",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=13).",
        "visual_detail": "A man aged 18-60, viewed from the side, wearing long coat, trousers, carrying backpack, wearing hat.",
        "occurrence_time": "2026-03-02 00:28:47",
    },
    {
        "title": "Status: Area Secure",
        "system_label": "The last unknown subject has left the monitored area.",
        "visual_detail": "",
        "occurrence_time": "2026-03-02 00:28:50",
    },
    {
        "title": "Enter Area: dung",
        "system_label": "Recognized as a registered person in the system (ID=1003, score=0.820, votes=5).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing short-sleeve top, trousers, carrying backpack.",
        "occurrence_time": "2026-03-05 08:12:03",
    },
    {
        "title": "Left Area: dung",
        "system_label": "Registered member left the monitored area (Track ID=21).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing short-sleeve top, trousers, carrying backpack.",
        "occurrence_time": "2026-03-05 08:45:27",
    },
    {
        "title": "Enter Area: dung",
        "system_label": "Recognized as a registered person in the system (ID=1003, score=0.790, votes=4).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing long-sleeve top, trousers.",
        "occurrence_time": "2026-03-10 18:05:12",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=31, votes=3).",
        "visual_detail": "A woman aged 18-60, viewed from the side, wearing skirt or dress, carrying handbag.",
        "occurrence_time": "2026-03-10 18:05:20",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=32, votes=3).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing short-sleeve top, trousers.",
        "occurrence_time": "2026-03-10 18:05:25",
    },
    {
        "title": "Left Area: dung",
        "system_label": "Registered member left the monitored area (Track ID=30).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing long-sleeve top, trousers.",
        "occurrence_time": "2026-03-10 21:12:03",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=31).",
        "visual_detail": "A woman aged 18-60, viewed from the back, wearing skirt or dress, carrying handbag.",
        "occurrence_time": "2026-03-10 21:12:10",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=32).",
        "visual_detail": "A man aged 18-60, viewed from the side, wearing short-sleeve top, trousers.",
        "occurrence_time": "2026-03-10 21:12:14",
    },
    {
        "title": "Status: Area Secure",
        "system_label": "The last unknown subject has left the monitored area.",
        "visual_detail": "",
        "occurrence_time": "2026-03-10 21:20:00",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=51, votes=3).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:05:12",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=51).",
        "visual_detail": "A man aged 18-60, viewed from the side, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:10:44",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=52, votes=3).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:18:03",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=52).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:22:10",
    },
    {
        "title": "Unknown Person Detected",
        "system_label": "Identity check completed with consistent recognition results (Track ID=52, votes=3).",
        "visual_detail": "A man aged 18-60, viewed from the front, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:23:03",
    },
    {
        "title": "Left Area: Unknown Person",
        "system_label": "Unidentified subject left the monitored area (Track ID=52).",
        "visual_detail": "A man aged 18-60, viewed from the back, wearing short-sleeve top, trousers, carrying shoulder bag.",
        "occurrence_time": "2026-03-20 19:25:10",
    },
]


def seed_mock_logs() -> int:
    conn = get_postgres_connection(debug=True)
    if conn is None:
        print("Cannot connect to PostgreSQL.")
        return 0

    embedder = Embedder()
    inserted_rows = 0

    for item in MOCK_LOGS:
        log_row = {
            "id": str(uuid.uuid4()),
            "title": item["title"],
            "system_label": item["system_label"],
            "visual_detail": item["visual_detail"],
            "occurrence_time": item["occurrence_time"],
            "file_path": "",
        }
        embedding = embedder.embed_log(log_row)
        log_row["embedding"] = embedding

        inserted_rows += insert_rows(
            table_name="logs",
            data={k: [v] for k, v in log_row.items()},
            conn=conn,
            debug=False,
        )

    conn.close()
    print(f"Inserted {inserted_rows} mock logs.")
    return inserted_rows


if __name__ == "__main__":
    seed_mock_logs()
