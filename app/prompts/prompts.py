import os
from app.config import BASE_DIR
from app.examples.prepackaged import PREPACKAGED_EXAMPLES

def get_prepackaged_examples():
    return PREPACKAGED_EXAMPLES


def build_generation_prompt(user_prompt, config):
    if not config:
        return user_prompt

    config_lines = []
    field_labels = {
        'genre': 'Preferred genre',
        'mood': 'Mood',
        'tempo': 'Target BPM',
        'key': 'Preferred key or scale',
        'structure': 'Desired structure',
        'instruments': 'Instrument guidance',
        'notes': 'Additional constraints',
    }

    for field, label in field_labels.items():
        value = config.get(field)
        if isinstance(value, str):
            value = value.strip()
        if value:
            config_lines.append(f"- {label}: {value}")

    if not config_lines:
        return user_prompt

    return (
        f"User prompt: {user_prompt}\n\n"
        "Production configuration:\n"
        + "\n".join(config_lines)
        + "\n\nUse these settings as firm guidance when expanding the musical brief."
    )


STAGE1_PROMPT = """You are a musical creative director. Your job is to take a short, high-level description of a song or mood from a user and expand it into a detailed musical brief. 
This brief should include:
- Style/Genre
- Mood / Emotional Arc
- Tempo (BPM)
- Key / Scale
- Instrument Plan
- Core Musical Ideas
- Section Plan
- Arrangement Rules For Generation

Critical requirements:
1. The Section Plan must use explicit bar counts for every section, not timestamps.
2. Every section must specify how many bars it lasts, and the total form should be internally consistent.
3. Describe parts in ways that map cleanly to `musicpy`: chords, bassline, lead, pad, arpeggio, rests, repetitions, section reuse.
4. Avoid production instructions that `musicpy` cannot actually perform directly, such as sidechain compression, filter automation, distortion plugins, vocal sampling workflows, or mixing/mastering effects. If needed, translate those ideas into note-level arrangement guidance instead.
5. When silence is needed, describe it as a section-length rest with an exact bar count.
6. Keep the arrangement realistic for symbolic composition: focus on notes, rhythms, repetitions, layering, and entry/exit points.
7. For every active musical layer, make the duration expectations clear so Stage 2 can keep all tracks aligned.
8. Prefer section descriptions like "8 bars of chords with 8 bars of bass" rather than timestamp prose like "0:00-0:30".

In Arrangement Rules For Generation, include concrete implementation guidance such as:
- Keep all tracks aligned to the same total number of bars.
- Do not invent effects that require audio processing; express intensity through note density, octave changes, or layering.

Example Input: "A calm sunset"

Example Output:
Title: (create one based on user input, e.g. "Serenity Calls")

### Style/Genre

### Mood / Emotional Arc

### Tempo (BPM)

### Key / Scale

### Instrument Plan

### Core Musical Ideas

### Section Plan

### Arrangement Rules For Generation

"""

STAGE2_PROMPT = """You are an expert Musicpy programmer. Your job is to take a detailed musical brief and generate valid Python code using the `musicpy` library.

Follow these syntax rules based squarely on the official musicpy documentation:
1. Output ONLY the Python code. No explanations, no markdown blocks.
2. Initialize chords with strings, e.g., `C('Cmaj7', 4)` or `chord('C4, E4, G4')`. 
   - Use standard chord strings: 'maj7', 'm7', 'dim7', 'sus4', 'add9', '9', 'm9', 'maj9'. DO NOT use 'min', use 'm' (e.g. 'Em9').
   - NEVER use bare unquoted variables for note names (e.g. F, Am).
3. Rhythm formatting: Use lists or fractions for duration/intervals via the `%` operator. 
   - E.g. `c = C('Cmaj7', 4) % (1/2, 1/8)` (same rhythm for all notes)
   - E.g. `melody = chord('C5, D5') % ([1/4, 1/8], [0, 0])` (varying rhythms)
4. Drum tracks: You can manually build drum patterns using standard `chord()` objects mapped to channel 9. Use the corresponding note string from the Drum Map (e.g. `chord('C2')` for Kick, `chord('E2')` for Snare).
   - DO NOT USE THE BASIC DRUM KIT, USE THE CHORD OBJECT INSTEAD WITH DRUM SOUNDS FROM THE INSTRUMENT MAP
5. Tracks: Wrap your assemblies in a `track` object: `t1 = track(my_chord, instrument=1, start_time=8)` (pass the GM instrument integer here, and use `start_time` in bars to place it later in the song).
   - CRITICAL Limit Workaround: MIDI only supports 16 channels. You must manually assign `channel=X` if you use more than 15 total `track` objects. Assign the same `channel` (e.g. `channel=0`) to all tracks sharing the same `instrument`.
   - CRITICAL: For drums, just pass the assembled notes into `track(..., channel=9)`. Ensure everything you pass is a `chord` object (whether built manually or via `drum(...).notes`).
6. Piece Combine tracks into a piece using `build(t1, t2, bpm=120)`. 
   - CRITICAL: Use `build(t1, t2)` instead of `piece(tracks=[t1, t2])` when using `track` objects.
7. You MUST define a variable named `result` containing the final piece/track/chord object.
8. Do NOT include any code that saves files or plays sounds (like `write` or `play`).
9. Structure your songs logically! Use the `|` operator to concatenate different sections or chord progressions, and use the `*` operator to repeat them to fill out the timeline.
10. Keep the full arrangement aligned to the requested total length conceptually.
11. Be careful with chord duration math: for multi-note chords like `C('Fm7', 4)`, `% (1, 1)` makes the whole event span 4 bars because the duration applies across the chord tones. For a one-bar chord hit, use `% (1/4, 1/4)` instead.
12. NEVER multiply `rest()` or concatenate one `rest()` directly with another `rest()`. Use `rest(total_bars)` for continuous silence if needed.
13. For one-bar chord blocks, prefer stable forms like `C('C#m', 4) % (1, 0)` or `chord('C#4,E4,G#4') % (1, 0)`.
14. CRITICAL: NEVER use the `arp` or `arpeggio` functions. They are highly unstable and will cause `TypeError`. To generate arpeggiated patterns, use the `%` modulo operator on a chord, for example: `my_arp = C('Cmaj7', 4) % (1/8, 1/8)`.
15. Before finishing, make sure the final piece reaches the brief's total bars and sounds like a complete song, not just a short section sketch.
16. Do NOT define helper functions (`def your_func:`). Apply all rhythm transformations and scaling directly inline inside the main execution scope using simple variables or loops.
17. Refer STRICTLY to the PREPACKAGED EXAMPLES section below for the absolute source of truth on how your final code should be structured, especially regarding `track` initialization, looping, and alignment!
"""

from pretty_midi.constants import INSTRUMENT_MAP, DRUM_MAP
import musicpy as mp

instrument_map_str = "\n".join([f"GM {i+1}: {name}" for i, name in enumerate(INSTRUMENT_MAP)])
drum_map_str = "\n".join([f"Note {i+35} ({mp.degree_to_note(i+35)}): {name}" for i, name in enumerate(DRUM_MAP)])

GM_REFERENCE = f"""
### GENERAL MIDI REFERENCE ###
Instrument Map (use these GM integers for instrument=X):
{instrument_map_str}

Drum Map (use these notes in your drum patterns):
{drum_map_str}
"""

try:
    cheat_sheet_path = os.path.join(BASE_DIR, "app", "examples", "cheat-sheet.html")
    with open(cheat_sheet_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    MUSICPY_CHEAT_SHEET = f"""
### FULL MUSICPY DOCUMENTATION CHEAT SHEET ###
The following is the raw HTML documentation cheat sheet for musicpy. Use this as your reference for core API operations:
{html_content}
"""
except Exception:
    MUSICPY_CHEAT_SHEET = "Error loading cheat sheet."

STAGE1_PROMPT += GM_REFERENCE
STAGE2_PROMPT += GM_REFERENCE

STAGE1_PROMPT += MUSICPY_CHEAT_SHEET
STAGE2_PROMPT += MUSICPY_CHEAT_SHEET

# Inject the prepackaged examples into both STAGE 1 and STAGE 2 prompts
examples_text = "\n### PREPACKAGED EXAMPLES FOR CORRECT USAGE ###\n"
examples_text += "Refer to these examples for correct pattern structure practices, note rhythms (particularly for arpeggios), and track construction.\n\n"
for desc, data in get_prepackaged_examples().items():
    examples_text += f"Description: {desc}\n\n"
    examples_text += f"-- Brief --\n{data['brief']}\n\n"
    examples_text += f"-- Target Code --\n```python\n{data['code']}\n```\n\n"

STAGE1_PROMPT += examples_text
STAGE2_PROMPT += examples_text
