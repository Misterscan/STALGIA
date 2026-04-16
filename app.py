import os
import sys

# macOS Apple Silicon (Homebrew) fix for finding FluidSynth
if sys.platform == 'darwin' and os.path.isdir('/opt/homebrew/lib'):
    # Prepend Homebrew's lib dir so ctypes.util.find_library can find it
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib' + (
        ':' + os.environ['DYLD_FALLBACK_LIBRARY_PATH'] if 'DYLD_FALLBACK_LIBRARY_PATH' in os.environ else ''
    )

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(port=5055, debug=True)
