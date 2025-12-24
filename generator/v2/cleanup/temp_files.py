# generator/v2/cleanup/temp_files.py

import os
from generator.v2.cleanup.models import TempFilesContext


def cleanup_temp_files(ctx: TempFilesContext) -> None:
    """
    Elimina archivos temporales declarados explícitamente.
    """
    for path in ctx.files:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    if ctx.directories:
        for d in ctx.directories:
            if os.path.isdir(d):
                try:
                    for f in os.listdir(d):
                        p = os.path.join(d, f)
                        if os.path.isfile(p):
                            os.remove(p)
                except Exception:
                    pass
