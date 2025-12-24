from generator.v2.content import selector_db

def test_selector_avoids_recently_used(monkeypatch, tmp_path):
    # -----------------------------------
    # Arrange filesystem
    # -----------------------------------
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

    # -----------------------------------
    # Fake DB response
    # -----------------------------------
    def fake_obtener_usados_db(**kwargs):
        return {"oracion_1"}, {"Texto uno"[:80]}

    monkeypatch.setattr(
        selector_db,
        "_obtener_usados_db",
        fake_obtener_usados_db
    )

    # -----------------------------------
    # Act
    # -----------------------------------
    path, base_name = selector_db.elegir_texto_para(
        channel_id=7,
        format_key="short_oracion",
        channel_config=channel_config
    )

    # -----------------------------------
    # Assert
    # -----------------------------------
    assert base_name == "oracion_2"