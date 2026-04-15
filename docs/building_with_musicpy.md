# Building with Musicpy

STALGIA relies on the **[musicpy](https://github.com/musicpy-dev/musicpy)** library to bridge the gap between concept and audio. If you're interested in how the underlying music generation works, or if you want to build your own text-to-music platform, understanding `musicpy` is the first and most important step.

## What is Musicpy?

`musicpy` is a domain-specific language (DSL) and engine embedded within Python. Instead of manipulating raw audio waveforms (which is computationally heavy and often yields muddy, unpredictable results from AI models), `musicpy` allows you to define music **symbolically**. 

It treats musical elements—notes, chords, rests, and drum beats—as programmable Python objects. You can perform arithmetic on these objects to sequence timing, stack them to create harmony, or iterate over them to generate loops. 

## How Musicpy Works

To translate code into music, `musicpy` relies on a few core concepts and extensive operator overloading:

### 1. Musical Primitives
Everything starts with basic musical structures:
- **Chords:** Defined easily via chord names, like `C('Cmaj7', 4)` (a C major 7th chord in the 4th octave).
- **Melodies:** Defined by listing notes `chord('C5, D5, E5')`.
- **Drums:** Defined using rhythmic character strings, such as `drum('K, H, S, H')` (Kick, Hi-hat, Snare, Hi-hat).

### 2. Time and Rhythm (The `%` Operator)
`musicpy` uses the modulo operator (`%`) to apply durations and intervals to notes and chords. 
- `C('Am7', 4) % (1/2, 1/8)` applies a specific note length (1/2 bar) and stepping interval between notes (1/8 bar).
- `chord('C5, D5') % ([1/4, 1/4], [0, 0])` assigns exact individual lengths and spacings to multiple notes in a sequence.

### 3. Arrangement and Sequencing
Python's standard operators are overridden to intuitively place music blocks together:
- `|` (Bitwise OR): Concatenates sequences sequentially (e.g., `intro_chords | verse_chords`).
- `*` (Multiplication): Loops sequences a set number of times (e.g., `verse_chords * 4`).
- `&` (Bitwise AND): Stacks layers simultaneously.

### 4. Tracks and Pieces
Once you've built your sequences, you assign them to a `track()` with an explicit `start_time` (in bars) and a General MIDI `instrument` integer (e.g., `instrument=1` for Piano, `channel=9` for drums). Finally, you compile all tracks together using `build(track1, track2, bpm=120)`.

---

## How to Build a STALGIA-like Product

If you want to build your own AI-to-Code music generator, you can replicate the STALGIA pipeline using these four core pillars:

### Step 1: The NLP Translation Layer (Prompt Engineering)
LLMs are excellent at writing Python, but `musicpy`'s syntax is highly specific. 
- **Expand the Concept:** Have the LLM first act as a "Creative Director" mapping out the song's BPM, bar counts, and instruments.
- **Enforce Syntax Rules:** Pass the expanded brief to a second LLM constrained by rigorous rules (e.g., "Never concatenate a drum sequence with a rest()", "Initialize chords using strings"). 
- **Goal:** The LLM's only job is to output a raw python string that produces a `result` variable containing the final `musicpy` arrangement.

### Step 2: Safe Code Execution & Retry Loops
You must execute the generated Python string on your server:
- Use Python's `exec(generated_code, global_namespace)` to compile the sequence in memory.
- **Crucial:** LLMs will occasionally hallucinate arguments or cause `SyntaxError`s. Wrap the execution in a `try/except` block. If it fails, capture the Python traceback and send it *back* to the LLM, asking it to fix its mistake. This self-correction loop vastly increases generation success rates.

### Step 3: MIDI Output & Audio Rendering
Once the snippet executes successfully, you have a `musicpy` object. 
- Call `write(result, name="output.mid")` to generate standard MIDI.
- To produce listenable audio (MP3/WAV), utilize the `musicpy.daw` module. Load a Soundfont (`.sf2` file, like `TimGM6mb.sf2`) and map it to your tracks. Render the arrangement into a `BytesIO` buffer stream to send directly to your user's browser without saving bloated audio files to your server disk. 

### Step 4: The Frontend Experience
Use standard HTML5 Audio components or libraries like `html-midi-player` to let users interact with the final result. Because you generated the music via code (symbolically), you can effortlessly display sheet music, piano rolls, or the exact Python code right alongside the audio track, making your product significantly more transparent and editable than black-box AI audio generators.