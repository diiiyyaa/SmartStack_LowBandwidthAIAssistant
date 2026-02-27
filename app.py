from flask import Flask, render_template, request
import json
import re
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
from rapidfuzz import fuzz
from voice.speak import speak

# Load Whisper model (use "tiny" if low RAM)
model = WhisperModel("base")

app = Flask(__name__)

# -------------------------
# Load JSON data per language
# -------------------------
def load_data(lang):
    try:
        with open(f"data/data_{lang}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# -------------------------
# Clean text
# -------------------------
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u0900-\u097F\u0B80-\u0BFF\u0980-\u09FF\u0A80-\u0AFF]", "", text)
    return text


# -------------------------
# Category Detection
# -------------------------
def detect_category(query):
    query = query.lower()

    if any(word in query for word in ["wheat", "rice", "fertilizer", "crop", "soil", "irrigation", "pest"]):
        return "🌾 Agriculture"

    elif any(word in query for word in ["fever", "headache", "medicine", "doctor"]):
        return "🩺 Health"

    elif any(word in query for word in ["pm kisan", "scheme", "loan", "kisan credit", "insurance"]):
        return "🏛 Government Scheme"

    elif any(word in query for word in ["exam", "school", "study"]):
        return "📚 Education"

    else:
        return "🔍 General"

# -------------------------
# Smart response with language support
# -------------------------
def get_response(query, lang):
    data = load_data(lang)
    query = clean_text(query)

    best_score = 0
    best_answer = None

    for key, answer in data.items():

        # Clean key properly (important for Hindi/Tamil etc.)
        formatted_key = clean_text(key.replace("_", " "))

        # First check direct match (very important)
        if formatted_key in query:
            return answer

        # Better fuzzy matching
        score = max(
            fuzz.token_set_ratio(query, formatted_key),
            fuzz.partial_ratio(query, formatted_key)
        )

        if score > best_score:
            best_score = score
            best_answer = answer

    print("Query:", query)
    print("Best Score:", best_score)

    if best_score >= 60:
        return best_answer

    fallback_messages = {
        "en": "Sorry, I could not understand. Please ask about farming, health, or schemes.",
        "hi": "माफ़ कीजिए, मैं समझ नहीं पाई। कृपया खेती, स्वास्थ्य या योजनाओं के बारे में पूछें।",
        "mr": "माफ करा, मला समजले नाही. कृपया शेती, आरोग्य किंवा योजनांबद्दल विचारा.",
        "bn": "দুঃখিত, আমি বুঝতে পারিনি। দয়া করে কৃষি, স্বাস্থ্য বা সরকারি প্রকল্প সম্পর্কে জিজ্ঞাসা করুন।",
        "ta": "மன்னிக்கவும், எனக்கு புரியவில்லை. தயவுசெய்து விவசாயம், ஆரோக்கியம் அல்லது திட்டங்கள் பற்றி கேளுங்கள்.",
        "gu": "માફ કરશો, હું સમજી શકી નહીં. કૃપા કરીને ખેતી, આરોગ્ય અથવા યોજનાઓ વિશે પૂછો."
    }

    return fallback_messages.get(lang, fallback_messages["en"])

# -------------------------
# Voice input (Offline Whisper)
# -------------------------
def listen_from_mic(lang):
    filename = f"temp_{uuid.uuid4().hex}.wav"
    duration = 5  # seconds

    recording = sd.rec(int(duration * 16000), samplerate=16000, channels=1)
    sd.wait()

    wav.write(filename, 16000, recording)

    segments, info = model.transcribe(
        filename,
        language=lang   # Force language detection
    )

    text = ""
    for segment in segments:
        text += segment.text

    os.remove(filename)
    return text.strip()

# -------------------------
# Main Route
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    spoken_text = ""
    audio_file = None
    category = ""

    if request.method == "POST":
        lang = request.form["language"]

        if "voice" in request.form:
            spoken_text = listen_from_mic(lang)
        else:
            spoken_text = request.form["query"]

        response = get_response(spoken_text, lang)
        category = detect_category(spoken_text)

        audio_file = speak(response, lang)

    return render_template(
        "index.html",
        response=response,
        spoken_text=spoken_text,
        audio_file=audio_file,
        category=category
    )

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)