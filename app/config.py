import os
import pretty_midi

BASE_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SF2_PATH = os.path.normpath(os.path.join(os.path.dirname(pretty_midi.__file__), "TimGM6mb.sf2"))

