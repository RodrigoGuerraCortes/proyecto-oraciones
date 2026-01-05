# generator/v3/generator/utils/voice_ab.py

def decidir_tts_para_video(
    *,
    porcentaje: float,
    seed: str
) -> bool:
    """
    Decisión determinística basada en seed.
    porcentaje: 0.20 → 20%
    """

    print(f"[DECIDE] Decidiendo TTS para video con porcentaje={porcentaje} y seed={seed}")
    
    h = abs(hash(seed)) % 100
    return h < int(porcentaje * 100)
