<div align="center">

# Getting Started
<img src="../static/logo.png" alt="STALGIA Logo">

This guide explains how to install dependencies and run STALGIA on your local machine.

</div>

## Prerequisites

1. **Python 3.10+**: Ensure Python is installed and accessible in your system `PATH`.
2. **FluidSynth (System Audio Library)**: REQUIRED for MIDI-to-Audio background rendering. You must install the system-level C library, not just the python package:
   - **macOS:** `brew install fluidsynth`
   - **Linux:** `sudo apt install fluidsynth`
   - **Windows:** Download the [compiled release](https://github.com/FluidSynth/fluidsynth/releases) and add the `bin` directory to your System `PATH`.
3. **Google Gemini API Key**: Visit the [Google AI Studio](https://aistudio.google.com/) to obtain an API key for access to `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite-preview`.

## Installation

1. **Clone the repository.**
2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```
3. **Activate the virtual environment:**
   - **Windows (PowerShell):** 
   ```Powershell
   .\.venv\Scripts\Activate.ps1
   ```
   - **macOS/Linux:** 
   ```bash
   source .venv/bin/activate
   ```
4. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `musicpy`, `google-genai`, `flask`, `flask-cors`, `flasgger`, `pretty_midi`, and `audioop-lts` (for Python 3.13+ compatibility) are installed.*

## Configuration

Set the `GEMINI_API_KEY` system environment variable before starting the app.

- **Windows:**
  ```powershell
  $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
  ```
- **macOS/Linux:**
  ```bash
  export GEMINI_API_KEY="YOUR_API_KEY_HERE"
  ```

**Soundfont Note:**
The audio export mechanism relies on an `.sf2` soundfont provided by `pretty_midi`. The system automatically resolves its dynamic path (e.g. `pretty_midi/TimGM6mb.sf2`) directly from the installed package.

## Running the Application

Start the Flask development server from the root directory:

```bash
python app.py
```

Wait a few seconds for the application bundle to load. Open a web browser and navigate directly to:
- **Main App Interface**: `http://127.0.0.1:5001/` (Served dynamically by the Flask root route, no need for separate file hosting!)
- **Interactive API Docs (Swagger)**: `http://127.0.0.1:5001/apidocs/`
