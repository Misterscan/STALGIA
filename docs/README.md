<div align="center">

# STALGIA

<img src="../static/logo.png" alt="STALGIA Logo">

**STALGIA** is a musical environment that translates conversational prompts into fully-fledged, executable Python code using the [`musicpy`](https://github.com/Rainbow-Dreamer/musicpy) library. Rather than generating raw audio from a black box, STALGIA relies purely on Python code to sequence notes, chords, and rhythms, turning your specifications into high-quality MIDI and audio files.

</div>

## Features

- **Code-Driven Music Generation:** All music is explicitly sequenced via Python syntax using `musicpy`, ensuring the output is perfectly structured, readable, and editable.
- **Natural Language Translation:** Employs a dual-stage NLP process to expand high-level descriptions into a musical brief and reliably translate them into executable Python code.
- **Pre-packaged Examples:** Includes a fast-path mechanism to instantly bypass LLM generation and serve guaranteed-quality base code blocks when a user selects a preset example from the frontend.
- **Configurable Attributes:** Provide genre, tempo, instruments, key, and mood for precise structural control over the generated composition.
- **Syntactic Robustness:** The backend translator explicitly limits the LLM's usage of crash-inducing `musicpy` edge cases (e.g., prohibiting `.arp()`, manually bounding the 16-channel MIDI limit, enforcing `.notes` conversion on drum maps, and avoiding raw `rest` multiplication).
- **Modular Pipeline:** Extensible Flask application featuring independent APIs and separated concerns.
- **DAW Rendering:** In-memory sequence rendering from Python code straight into MP3, WAV, or MIDI formats using a dynamic multi-channel SF2 soundfont (`pretty_midi`), returning background-rendered audio streams instantly to the UI's HTML5 Audio elements.

## Documentation Index

- [Getting Started](getting_started.md) — Pre-requisites, Installation, and execution commands.
- [Architecture](architecture.md) — How the two-stage generation pipeline and file layout function.
- [Building with Musicpy](building_with_musicpy.md) — What Musicpy is, how its syntax works, and how to build STALGIA-like products.
- [API Reference](api_reference.md) — Available REST endpoints and request/response shapes.

## Production Credits

**STALGIA** is not just a theoretical environment; it is a core component of the Misterscan production pipeline. The lead single Lifeline (2026) from the upcoming album 2007 Horizon was composed using the STALGIA engine, with final arrangement and mastering completed in FL Studio.
