import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from generator.v3.bots.pin_comment.ai.generator import generate_pin_comment

context = {
    "channel_name": "Oraciones Católicas",
    "video_tipo": "oración",
    "video_texto_base": (
        "Señor, pongo en tus manos mis preocupaciones "
        "y confío en que tu paz me sostendrá hoy."
    ),
}

result = generate_pin_comment(context)

print("=== PIN COMMENT GENERADO ===")
print(result["text"])
print("Model:", result["model"])
print("Prompt:", result["prompt_version"])
