
from generator.v2.content.selector_db import elegir_texto_para

def test_selector_returns_valid_file(tmp_path):
    # Arrange
    base = tmp_path / "textos"
    oraciones = base / "oraciones"
    oraciones.mkdir(parents=True)

    (oraciones / "oracion_1.txt").write_text("Texto uno")
    (oraciones / "oracion_2.txt").write_text("Texto dos")

    channel_config = {
        "content": {
            "base_path": str(base)
        },
        "formats": {
            "short_oracion": {
                "content": {
                    "type": "plain",
                    "path": "oraciones"
                }
            }
        }
    }

    # Act
    path, base_name = elegir_texto_para(
        channel_id=7,
        format_key="short_oracion",
        channel_config=channel_config,
        db_conn=None  # no DB
    )

    # Assert
    assert path.endswith(".txt")
    assert base_name.startswith("oracion_")


