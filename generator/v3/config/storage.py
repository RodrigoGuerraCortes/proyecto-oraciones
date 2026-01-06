# generator/v3/config/storage.py

import os

BASE_STORAGE_PATH = os.getenv(
    "BASE_STORAGE_PATH",
    "/mnt/storage",
)
