<div align="center">

# API Reference

<img src="../static/logo.png" alt="STALGIA Logo">

</div>

**Interactive API Documentation (Swagger UI)** is available natively! Run the application and navigate to `http://localhost:5055/apidocs/` in your browser to explore, test, and interact with these endpoints dynamically.

The backend uses a standard REST framework. Endpoints handle data queries, prompt execution, and dynamic file transmission.

## Get Tags (`/tags`)

Fetches JSON files from the `tags/` directory to populate frontend selection categories, except for instruments. The `instruments` array returned by this endpoint is sourced dynamically and authoritatively from the built-in `pretty_midi.constants.INSTRUMENT_MAP` and `DRUM_MAP` dictionaries.

**HTTP Query**
```http
GET /tags
```

**JSON Response**
```json
{
  "genre": {
    "Lo-Fi": ["lofi hip hop", "chillhop"],
    "Electronic": ["synthwave", "ambient"]
  },
  "mood": { ... }
}
```

## Generate Music (`/generate`)

The primary endpoint that triggers the LLM expansion and audio generation routines. Expects a JSON payload.

**Generative Rules & Limitations (Enforced in Translation):**
- **Dynamic Tagging:** Instruments are fetched exclusively from `pretty_midi.constants.INSTRUMENT_MAP` and `DRUM_MAP`.
- **Constraint Boundaries:** Instrument bounds respect **16 total MIDI channels**, with Channel 9 reserved explicitly for percussion using General MIDI assignments.
- **Failovers:** Triggers `gemini-3.1-flash-lite-preview` dynamically if initial `gemini-3.1-pro-preview` translation throws execution errors, maxing at 3 total attempts.
- Syntactically, the LLM bypasses `arp()` and `arpeggio()` entirely due to execution instability, using modulus `%` stepping instead.
- Generates inline code strictly. Helper functions (`def func:`) are restricted.

**Example Query: Custom Generation**
```http
POST /generate
Content-Type: application/json

{
  "prompt": "A heroic battle theme",
  "config": {
    "genre": "Orchestral",
    "tempo": "120 BPM",
    "key": "C minor"
  }
}
```

**Example Query: Prepackaged Example Bypass**
To bypass the LLM and instantly retrieve a guaranteed output, send the exact string of a prepackaged example as the prompt:
```http
POST /generate
Content-Type: application/json

{
  "prompt": "A chill lo-fi hip hop beat at 80 BPM. Soft, jazzy electric piano seventh chords playing a relaxed progression, layered over a slow, simple drum beat.",
  "config": {}
}
```

**Success Response (200 OK)**
```json
{
  "brief": "### Style/Genre\nOrchestral.\n...",
  "code": "from musicpy import *\n...",
  "midi_url": "/download/midi"
}
```

**Failure Response (500 Error)**
```json
{
  "error": "Failed after 3 attempts. Last error: ...",
  "code": "from musicpy import *\n..."
}
```

## Download MIDI (`/download/midi`)

Streams the generated `.mid` output file back to the browser. Returns `Content-Disposition: attachment`.

**HTTP Query**
```http
GET /download/midi
```

## Download Audio (`/download/audio`)

Uses `musicpy`'s DAW synthesizer via soundfonts (`.sf2`) to export dynamic audio.

**HTTP Query Parameters**
- `format`: (Optional) `str`. Specifies the target audio extension. Defaults to `mp3`. (e.g., `wav`, `flac`)

**Example Queries**
```http
GET /download/audio?format=wav
GET /download/audio?format=mp3
```