# generator/content/license.py
import os

# =====================================================================
#   Licence para youtube
# =====================================================================
def leer_licencia_si_existe(path):
    if not path:
        return ""

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""

    return ""