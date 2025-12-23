# generator/publications/editorial_windows.py
from datetime import timedelta

# ======================================================
# Ventanas de reutilización POR PLATAFORMA
# (editorial profesional)
# ======================================================

PLATFORM_REUSE_DAYS = {
    1: 7,   # YouTube Shorts
    2: 3,   # Facebook Reels
    3: 3,   # Instagram Reels
    4: 2,   # TikTok
}

# ======================================================
# Bloqueo global anti-spam (NO editorial)
# ======================================================

GLOBAL_ANTISPAM_DAYS = 1  # 24 horas
