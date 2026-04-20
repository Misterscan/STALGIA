import io
import os
import traceback
from musicpy import read
from musicpy.daw import daw
from pydub import AudioSegment, effects
from app.config import SF2_PATH, BASE_DIR

def render_midi_to_audio(midi_filename="output.mid", format='mp3'):
    try:
        midi_path = os.path.join(BASE_DIR, midi_filename)
        current_piece = read(midi_path)
        
        d = daw(len(current_piece.tracks))
        
        # Load the same soundfont for all channels
        for i in range(len(current_piece.tracks)):
            d.load(i, SF2_PATH)
        
        audio_seg = d.export(current_piece, action='get')
        
        # Normalize audio to improve volume issues in browser
        # Ensure we're working with an AudioSegment if daw.export doesn't return one directly, 
        # though musicpy.daw.export usually returns a pydub AudioSegment when action='get'
        if isinstance(audio_seg, AudioSegment):
            audio_seg = effects.normalize(audio_seg)
        
        img = io.BytesIO()
        audio_seg.export(img, format=format)
        img.seek(0)
        
        return img
    except Exception as e:
        traceback.print_exc()
        raise e
