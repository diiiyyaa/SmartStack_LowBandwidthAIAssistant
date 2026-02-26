import os
import uuid
import subprocess

def speak(text, lang):

    model_map = {
        "en": "models/en_US-amy-medium.onnx",
        "hi": "models/hi_IN-rohan-medium.onnx",
    }

    model_path = model_map.get(lang, model_map["en"])

    output_file = f"static/audio_{uuid.uuid4().hex}.wav"

    piper_path = "C:/Users/HP/Downloads/piper_windows_amd64/piper/piper.exe"

    try:
        process = subprocess.Popen(
            [
                piper_path,
                "--model", model_path,
                "--output_file", output_file
            ],
            stdin=subprocess.PIPE
        )

        # 🔥 Encode text properly for Hindi Unicode
        process.communicate(text.encode("utf-8"))

        return output_file

    except Exception as e:
        print("TTS Error:", e)
        return None