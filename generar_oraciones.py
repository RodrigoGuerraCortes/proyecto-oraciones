import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_oracion(tipo):
    prompt = f"""
Genera una oración católica espiritual.
Tipo: {tipo}.
Instrucciones:
- Escríbela en español.
- Estilo calmado, reconfortante, lleno de fe.
- Extensión entre 120 y 180 palabras.
- No menciones citas bíblicas.
- No repitas ideas.
- Hazla profunda y emotiva.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    texto = response.choices[0].message.content
    return texto

if __name__ == "__main__":
    tipo_oracion = "Oración de la mañana"
    oracion = generar_oracion(tipo_oracion)

    # Guardar el texto en carpeta textos/
    ruta = "textos/oracion_manana.txt"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(oracion) # type: ignore

    print("Oración generada y guardada en:", ruta)

