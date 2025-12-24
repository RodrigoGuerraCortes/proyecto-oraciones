# tests/v2/cleanup/test_image_validator.py

from PIL import Image

from generator.v2.cleanup.image_validator import validate_images_in_directory


def create_valid_image(path):
    img = Image.new("RGB", (50, 50), "white")
    img.save(path)


def create_corrupt_image(path):
    path.write_bytes(b"not an image")


def test_validate_images_removes_corrupt(tmp_path):
    valid = tmp_path / "ok.png"
    corrupt = tmp_path / "bad.png"

    create_valid_image(valid)
    create_corrupt_image(corrupt)

    result = validate_images_in_directory(
        directory=str(tmp_path)
    )

    assert result["valid"] == 1
    assert result["removed"] == 1
    assert valid.exists()
    assert not corrupt.exists()


def test_validate_images_ignores_directories(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()

    result = validate_images_in_directory(
        directory=str(tmp_path)
    )

    assert result["valid"] == 0
    assert result["removed"] == 0


def test_validate_images_ignores_specific_files(tmp_path):
    valid = tmp_path / "ok.png"
    ignore = tmp_path / "vignette.png"

    create_valid_image(valid)
    create_corrupt_image(ignore)

    result = validate_images_in_directory(
        directory=str(tmp_path),
        ignore_files=["vignette.png"],
    )

    assert result["valid"] == 1
    assert result["removed"] == 0
    assert ignore.exists()


def test_validate_images_directory_not_found(tmp_path):
    result = validate_images_in_directory(
        directory=str(tmp_path / "nope")
    )

    assert result["error"] == "directory_not_found"
