# tests/test_decision_imagen.py
from generator.image.decision import decidir_imagen_video

def test_decidir_imagen_video(monkeypatch):

    def fake_selector(categoria):
        return ("jesus/30.png", categoria)

    monkeypatch.setattr(
        "generator.image.decision.elegir_imagen_por_categoria",
        fake_selector
    )

    ruta = decidir_imagen_video(
        tipo="oracion",
        titulo="Oración a Jesús",
        texto="Señor Jesús"
    )

    assert ruta == "jesus/30.png"
