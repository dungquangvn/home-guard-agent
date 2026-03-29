import os
from typing import Dict, List, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def get_postgres_connection(debug=False):
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD"),
            connect_timeout=5,
        )
        if debug:
            print("Connected to PostgreSQL successfully")
            print(f"conn is None: {conn is None}")
        return conn
    except (psycopg2.OperationalError, Exception) as e:
        if debug:
            print(f"PostgreSQL connection error: {e}")
        return None


def insert_rows(table_name, data, conn=None, debug=False):
    if not data:
        return 0

    def _to_pgvector_literal(value):
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(str(v) for v in value) + "]"
        return value

    columns = list(data.keys())
    # Convert column-oriented data {col: [1, 2]} to row tuples [(1,), (2,)]
    rows = list(zip(*[data[col] for col in columns]))

    embedding_idx = columns.index("embedding") if "embedding" in columns else None
    if embedding_idx is not None:
        formatted_rows = []
        for row in rows:
            row_values = list(row)
            row_values[embedding_idx] = _to_pgvector_literal(row_values[embedding_idx])
            formatted_rows.append(tuple(row_values))
        rows = formatted_rows

    num_rows = len(rows)

    col_names = ", ".join(columns)
    placeholders = ", ".join("%s::vector" if col == "embedding" else "%s" for col in columns)
    query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    created_conn = conn is None
    if created_conn:
        conn = get_postgres_connection(debug=debug)

    if not conn:
        return 0

    try:
        with conn.cursor() as cur:
            if debug:
                print(query)
                print(rows)
            cur.executemany(query, rows)
            conn.commit()
            if debug:
                print(f"Log commited")
                print(f"Inserted {num_rows} rows.")
    except Exception as e:
        if debug:
            print(f"Error: {e}")
        if created_conn:
            conn.rollback()
        return 0
    finally:
        if created_conn:
            conn.close()

    return num_rows
