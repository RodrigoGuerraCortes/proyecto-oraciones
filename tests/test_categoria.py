# tests/test_categoria.py
from generator.content.categoria import decidir_categoria_video

def test_categoria_jesus():
    cat = decidir_categoria_video(
        tipo="oracion",
        titulo="Oración a Jesús",
        texto="Señor Jesús, en ti confío"
    )
    assert cat == "jesus"


def test_categoria_maria():
    cat = decidir_categoria_video(
        tipo="oracion",
        titulo="Ave María",
        texto="Santa María madre de Dios"
    )
    assert cat == "maria"


def test_categoria_espiritu_santo():
    cat = decidir_categoria_video(
        tipo="oracion",
        titulo="Ven Espíritu Santo",
        texto="Llena los corazones de tus fieles"
    )
    assert cat == "espiritu_santo"
