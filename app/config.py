import os
from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SF2_PATH = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages", "pretty_midi", "TimGM6mb.sf2")

client = genai.Client(api_key=GEMINI_API_KEY)
