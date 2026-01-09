# db/connection.py

import os
import psycopg
from psycopg.rows import dict_row


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "video_scheduler_v3"),
        user=os.getenv("DB_USER", "scheduler"),
        password=os.getenv("DB_PASSWORD", "scheduler123"),
        row_factory=dict_row,
    )
