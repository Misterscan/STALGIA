import os
import pretty_midi
from google import genai

BASE_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SF2_PATH = os.path.normpath(os.path.join(os.path.dirname(pretty_midi.__file__), "TimGM6mb.sf2"))

