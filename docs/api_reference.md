# API Reference

The backend uses a standard REST framework. Endpoints handle data queries, prompt execution, and dynamic file transmission.

## Get Tags (`/tags`)

Fetches JSON files from the `tags/` directory to populate frontend selection categories.

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

**HTTP Query**
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
  "error": "Failed after 2 attempts. Last error: ...",
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