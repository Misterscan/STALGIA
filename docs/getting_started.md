<div align="center">

# Welcome to STALGIA

<img src="../static/logo.png" alt="STALGIA Logo">

# Getting Started

This guide explains how to install dependencies and run STALGIA on your local machine.

</div>

## Prerequisites

1. **Python 3.10+**: Ensure Python is installed and accessible in your system `PATH`.
2. **Google Gemini API Key**: Visit the [Google AI Studio](https://aistudio.google.com/) to obtain an API key for access to `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite-preview`.

## Installation

1. **Clone the repository.**
2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```
3. **Activate the virtual environment:**
   - **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
   - **macOS/Linux:** `source .venv/bin/activate`
4. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `musicpy`, `google-genai`, `flask`, `flask-cors`, and `pretty_midi` are installed.*

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
The audio export mechanism relies on an `.sf2` soundfont provided by `pretty_midi`. The default config searches for it within the local site-packages:
`.venv/Lib/site-packages/pretty_midi/TimGM6mb.sf2`

## Running the Application

Start the Flask development server from the root directory:

```bash
python app.py
```

Open a web browser and navigate to `http://127.0.0.1:5001` or wherever the server console specifies.