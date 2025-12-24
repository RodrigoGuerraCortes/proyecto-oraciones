# tests/v2/cleanup/test_temp_files.py

import os

from generator.v2.cleanup.temp_files import cleanup_temp_files
from generator.v2.cleanup.models import TempFilesContext


def test_cleanup_removes_declared_files(tmp_path):
    f1 = tmp_path / "tmp1.png"
    f2 = tmp_path / "tmp2.jpg"
    f1.write_text("x")
    f2.write_text("y")

    ctx = TempFilesContext(
        files=[str(f1), str(f2)]
    )

    cleanup_temp_files(ctx)

    assert not f1.exists()
    assert not f2.exists()


def test_cleanup_ignores_missing_files(tmp_path):
    f1 = tmp_path / "no_existe.png"

    ctx = TempFilesContext(
        files=[str(f1)]
    )

    # no debe lanzar excepción
    cleanup_temp_files(ctx)

    assert True  # llegó hasta acá


def test_cleanup_does_not_touch_other_files(tmp_path):
    keep = tmp_path / "keep.txt"
    remove = tmp_path / "remove.txt"

    keep.write_text("keep")
    remove.write_text("remove")

    ctx = TempFilesContext(
        files=[str(remove)]
    )

    cleanup_temp_files(ctx)

    assert keep.exists()
    assert not remove.exists()
