import traceback
import os
from google.genai import types
from musicpy import *
from app.config import client
from app.prompts.prompts import STAGE1_PROMPT, STAGE2_PROMPT, build_generation_prompt

PREPACKAGED_EXAMPLES = {
    "A chill lo-fi hip hop beat at 80 BPM. Soft, jazzy electric piano seventh chords playing a relaxed progression, layered over a slow, simple drum beat.": {
        "brief": "### Style/Genre\nDreamy Lo-Fi Hip Hop\n\n### Section Plan\n- **Intro**: 4 bars. Rhodes piano only.\n- **Verse**: 8 bars. Rhodes + drums.\n- **Chorus**: 8 bars. Rhodes + drums + warm synth lead.\n- **Outro**: 4 bars. Fading rhodes chords.\n*Total 24 bars (~1:12 minutes)*",
        "code": "from musicpy import *\n\nfull_rhodes = ((C('Dm9', 4) % (1, 0)) | (C('G13', 4) % (1, 0)) | (C('Cmaj9', 4) % (1, 0)) | (C('Am7', 4) % (1, 0))) * 6 # 24 bars total\nfull_drums = (drum('K, H, S, H, K, -, S, H') * 16).notes # 16 bars total\nchorus_melody = (chord('D5, E5, F5, G5') % (1/2, 1/2)) * 4 # 8 bars total\n\nt1 = track(full_rhodes, instrument=5, start_time=0)\nt2 = track(full_drums, channel=9, start_time=4)\nt3 = track(chorus_melody, instrument=81, start_time=12)\nresult = build(t1, t2, t3, bpm=80)"
    },
    "An upbeat, driving 80s synthwave track at 130 BPM. It features a fast, pulsing 16th-note synth bassline, a catchy bright synthesizer melody, and a driving four-on-the-floor drum beat.": {
        "brief": "### Style/Genre\nUpbeat Synthwave / Synth-Pop\n\n### Section Plan\n- **Intro**: 8 bars. Driving bassline only.\n- **Build**: 8 bars. Bass + 4-on-the-floor drums.\n- **Drop / Chorus**: 16 bars. Add catchy sawtooth lead melody.\n- **Outro**: 8 bars. Bass fading out alone.\n*Total 40 bars (~1:13 minutes)*",
        "code": "from musicpy import *\n\nbass_pattern = chord('C2, C2, C2, C2, G1, G1, G1, G1') % (1/16, 1/16) # 1/2 bar\nfull_bass = bass_pattern * 80 # 40 bars total\ndance_drums = (drum('K, H, S, H, K, H, S, H') * 24).notes # 24 bars total\nmelody_loop = (chord('C5, G5, -, F5, D#5, -, D5, C5') % (1/8, 1/8)) * 16 # 16 bars total\n\nt1 = track(full_bass, instrument=40, start_time=0)\nt2 = track(dance_drums, channel=9, start_time=8)\nt3 = track(melody_loop, instrument=82, start_time=16)\nresult = build(t1, t2, t3, bpm=130)"
    },
    "A slow, grandiose cinematic string progression at 60 BPM. Long, sustained minor and major chords swelling out slowly to create a sense of scale and heroism.": {
        "brief": "### Style/Genre\nCinematic Orchestral Build\n\n### Section Plan\n- **Intro**: 8 bars. Deep cello and bass strings establishing chords.\n- **Main Swell**: 16 bars. Introduce high octave violin strings for heroism.\n- **Outro**: 8 bars. Soft resolution back to only lower strings.\n*Total 32 bars (~2:08 minutes)*",
        "code": "from musicpy import *\n\nintro_strings = (C('Cm', 4) % (2, 0)) | (C('Ab', 4) % (2, 0)) | (C('Eb', 4) % (2, 0)) | (C('Bb', 3) % (2, 0)) # 8 bars\nfull_strings = intro_strings * 4 # 32 bars total\n\nhigh_strings = (C('Cm', 5) % (2, 0)) | (C('Ab', 5) % (2, 0)) | (C('Eb', 5) % (2, 0)) | (C('Bb', 4) % (2, 0))\nmain_high_strings = high_strings * 2 # 16 bars total\n\nt1 = track(full_strings, instrument=49, start_time=0)\nt2 = track(main_high_strings, instrument=48, start_time=8)\nresult = build(t1, t2, bpm=60)"
    },
    "A fast and aggressive pop punk rock loop at 160 BPM. Distorted electric guitar power chords playing eighth notes, over loud rock drum patterns.": {
        "brief": "### Style/Genre\nEnergetic Pop Punk\n\n### Section Plan\n- **Intro**: 4 bars. Solo aggressive rock drum beat.\n- **Verse**: 16 bars. Distorted guitar rhythm chug + drums.\n- **Chorus**: 16 bars. Add high octave lead guitar for width.\n- **Outro**: 8 bars. Just drums finishing the track.\n*Total 44 bars (~1:06 minutes)*",
        "code": "from musicpy import *\n\npower_chords = (C('C5', 3) % (1/8, 1/8) * 8) | (C('G5', 3) % (1/8, 1/8) * 8) | (C('A5', 3) % (1/8, 1/8) * 8) | (C('F5', 3) % (1/8, 1/8) * 8) # 4 bars\nfull_guitars = power_chords * 8 # 32 bars\nfull_drums = (drum('K, -, S, -, K, K, S, -') * 44).notes # 44 bars\nlead_guitar = (chord('C5, D5, E5, C5') % (1/2, 1/2)) * 16 # 16 bars\n\nt1 = track(full_drums, channel=9, start_time=0)\nt2 = track(full_guitars, instrument=30, start_time=4)\nt3 = track(lead_guitar, instrument=29, start_time=20)\nresult = build(t1, t2, t3, bpm=160)"
    },
    "A delicate classical piece for solo acoustic grand piano at 100 BPM. It features fast, flowing A minor arpeggios that rise and fall gracefully.": {
        "brief": "### Style/Genre\nClassical Solo Piano\n\n### Section Plan\n- **Part A**: 8 bars. Soft cascading A minor / D minor arpeggios.\n- **Part B**: 8 bars. Tension shift using E minor climbs.\n- **Part A Return**: 8 bars. Resolve back to familiar motif.\n- **Outro**: 4 bars. Simple 4-bar sustain on A minor root.\n*Total 28 bars (~1:07 minutes)*",
        "code": "from musicpy import *\n\narp_am = chord('A3, C4, E4, A4, C5, A4, E4, C4') % (1/16, 1/16) * 2 # 1 bar\narp_dm = chord('D4, F4, A4, D5, F5, D5, A4, F4') % (1/16, 1/16) * 2 # 1 bar\narp_em = chord('E4, G4, B4, E5, G5, E5, B4, G4') % (1/16, 1/16) * 2 # 1 bar\n\nprog_A = (arp_am * 2) | (arp_dm * 2) # 4 bars\nprog_B = (arp_em * 2) | (arp_am * 2) # 4 bars\n\nfull_piece = prog_A * 2 | prog_B * 2 | prog_A * 2 # 24 bars\nend_chord = C('Am', 3) % (4, 0) # 4 bars (ringing out)\n\nt1 = track(full_piece | end_chord, instrument=1, start_time=0)\nresult = build(t1, bpm=100)"
    }
}

def generate_music(user_prompt, generation_config):
    # Short-circuit check for pre-packaged verified scripts
    exact_match = user_prompt.strip()
    if exact_match in PREPACKAGED_EXAMPLES:
        example_data = PREPACKAGED_EXAMPLES[exact_match]
        expanded_brief = example_data["brief"]
        music_code = example_data["code"]
        
        try:
            exec_globals = {}
            exec("from musicpy import *", exec_globals)
            exec(music_code, exec_globals)
            result_obj = exec_globals.get('result')
            write(result_obj, name="output.mid")
            
            return {
                'brief': expanded_brief,
                'code': music_code,
                'midi_url': '/download/midi'
            }
        except Exception as e:
            traceback.print_exc()
            return {'error': f"Pre-packaged execution failed: {str(e)}", 'code': music_code}

    combined_prompt = build_generation_prompt(user_prompt, generation_config)

    # Stage 1: Expand Prompt
    response1 = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        config=types.GenerateContentConfig(system_instruction=STAGE1_PROMPT, temperature=0.2, thinking_config=types.ThinkingConfig(thinking_level="low")),
        contents=[combined_prompt]
    )
    expanded_brief = response1.text
    print(f"Expanded Brief: {expanded_brief}")

    # Stage 2: Generate Code (with retry/fix logic)
    music_code = ""
    last_error = ""
    for attempt in range(2): # 1 initial + 1 retry
        prompt = expanded_brief if attempt == 0 else f"The following musicpy code failed with error: {last_error}. Please fix it and return the full corrected code.\n\nCode:\n{music_code}"
        
        response2 = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            config=types.GenerateContentConfig(system_instruction=STAGE2_PROMPT, temperature=0.3, thinking_config=types.ThinkingConfig(thinking_level="low")),
            contents=[prompt]
        )
        music_code = response2.text.strip()
        # Clean markdown if present
        if music_code.startswith("```python"):
            music_code = music_code.split("```python")[1].split("```")[0].strip()
        elif music_code.startswith("```"):
            music_code = music_code.split("```")[1].split("```")[0].strip()
        
        print(f"Attempt {attempt + 1} Generated Code:\n{music_code}")

        try:
            # Execute Code
            exec_globals = {}
            exec("from musicpy import *", exec_globals)
            exec(music_code, exec_globals)
            
            result_obj = exec_globals.get('result')
            if not result_obj:
                 raise ValueError('AI failed to generate a "result" variable')

            # Robust Type Handling for musicpy objects
            if isinstance(result_obj, scale):
                result_obj = chord(result_obj.notes)
            
            # Generate MIDI
            midi_filename = "output.mid" # Output to project root assuming running app.py from root
            write(result_obj, name=midi_filename)
            
            return {
                'brief': expanded_brief,
                'code': music_code,
                'midi_url': '/download/midi'
            }

        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 1:
                return {
                    'error': f"Failed after 2 attempts. Last error: {last_error}", 
                    'code': music_code
                }

    return {'error': "Unknown error occurred"}
