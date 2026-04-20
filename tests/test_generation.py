import pytest
from musicpy import *
import sys
import os

# Add parent dir to path for imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.prompts.prompts import build_generation_prompt
from app import create_app
from app.services import gemini_service

def test_musicpy_syntax_accuracy():
    """Verify that common Musicpy syntax pieces we expect AI to generate actually work."""
    try:
        # Test basic chord creation
        c = C('Cmaj7')
        assert str(c[0]) == 'C4'
        
        # Test rhythm application
        rhythm_chord = c @ [1, 1, 1, 1]
        assert len(rhythm_chord) == 4
        
        # Test piece creation
        p = piece(tracks=[rhythm_chord], bpm=120)
        assert p.bpm == 120
    except Exception as e:
        pytest.fail(f"Musicpy syntax changed or is broken: {e}")

def test_ai_guidelines_syntax_accuracy():
    """Verify that the exact example and rules provided in the AI generator prompt are valid."""
    try:
        # 1. Chords/Melodies
        piano_chords = C('Cmaj7', 4) % (1/2, 1/8) | C('Dm7', 4) % (1/2, 1/8)
        assert len(piano_chords) > 0
        melody = chord('C5, D5, E5, F5') % ([1/4]*4, [1/4]*4)
        assert len(melody) == 4

        # 2. Drums (Using empty beats `-` for rests, no instrument parameters)
        # Verify that appending to a rest via `|` raises TypeError to prevent regressions
        with pytest.raises(TypeError):
            r = rest(1/4) | drum('K')

        # Verifying correct usage:
        drum_pattern = drum('K, H, S, H, K, K, S, H')
        assert hasattr(drum_pattern, 'notes')

        # 3. Create Tracks (channel=9 for drums, instrument=X for others)
        # Note: drum.notes must be extracted because drum object has no track properties
        piano_track = track(piano_chords, instrument=1)
        synth_track = track(melody, instrument=81)
        drum_track = track(drum_pattern.notes, channel=9)
        assert getattr(drum_track, 'channel') == 9

        # 4. Combine into piece
        # Note: track object expects `content.notes`, so drums need `.notes` and piece() is actually build() when using track objects
        final_piece = build(piano_track, synth_track, drum_track, bpm=110)
        assert final_piece.bpm == 110
        assert len(final_piece.tracks) == 3
        
        # Write to ensure validity
        temp_file = "test_guideline.mid"
        write(final_piece, name=temp_file)
        assert os.path.exists(temp_file)
        os.remove(temp_file)
    except Exception as e:
        pytest.fail(f"AI Guideline syntax failed! Our prompt instructions are invalid: {e}")

def test_result_extraction_logic():
    """Simulate the exec() logic used in gemini_service.py to ensure it captures results."""
    code = """
from musicpy import *
guitar = C('Cmaj7') @ [1,2,3,4]
result = piece(tracks=[guitar], bpm=120)
    """
    exec_globals = {}
    exec("from musicpy import *", exec_globals)
    exec(code, exec_globals)
    
    assert 'result' in exec_globals
    assert isinstance(exec_globals['result'], piece)
    assert exec_globals['result'].bpm == 120

def test_random_song_generation_stability():
    """Test generating multiple variations to ensure no crashes occur with different musicpy objects."""
    variations = [
        "result = chord('C4,E4,G4')",
        "result = scale('C', 'major')",
        "result = piece(tracks=[chord('C4,E4,G4')], bpm=100)",
        "result = track(chord('C4,E4,G4') | chord('F4,A4,C5'))"
    ]
    
    for code in variations:
        exec_globals = {}
        exec("from musicpy import *", exec_globals)
        exec(code, exec_globals)
        assert 'result' in exec_globals
        
        res = exec_globals['result']
        if isinstance(res, scale):
            res = chord(res.notes)
            
        # Verify it can be written to MIDI without error
        write(res, name="test_temp.mid")
        assert os.path.exists("test_temp.mid")
        os.remove("test_temp.mid")

def test_comparison_tracks():
    """Comparison test: Ensure two different generations produce different MIDI content length or structure."""
    code1 = "result = chord('C4') @ [1,1]"
    code2 = "result = chord('C4') @ [1,1,1,1]"
    
    def get_len(code):
        eg = {}
        exec("from musicpy import *", eg)
        exec(code, eg)
        return len(eg['result'])
    
    assert get_len(code1) == 2
    assert get_len(code2) == 4


def test_build_generation_prompt_includes_config_fields():
    prompt = build_generation_prompt(
        'A cinematic piano theme',
        {
            'genre': 'Ambient',
            'tempo': '72',
            'structure': 'Intro, verse, chorus',
            'notes': 'Keep the intro sparse'
        }
    )

    assert 'User prompt: A cinematic piano theme' in prompt
    assert '- Preferred genre: Ambient' in prompt
    assert '- Target BPM: 72' in prompt
    assert '- Desired structure: Intro, verse, chorus' in prompt
    assert '- Additional constraints: Keep the intro sparse' in prompt


def test_build_generation_prompt_ignores_empty_config():
    assert build_generation_prompt('Just vibes', {}) == 'Just vibes'


def test_render_music_code_executes_user_edits(monkeypatch, tmp_path):
    output_file = tmp_path / 'output.mid'

    def fake_write(result_obj, name='output.mid'):
        assert result_obj is not None
        output_file.write_bytes(b'midi')

    monkeypatch.setattr(gemini_service, 'write', fake_write)

    result = gemini_service.render_music_code("""
```python
result = chord('C4,E4,G4')
```
""")

    assert result['midi_url'] == '/download/midi'
    assert "result = chord('C4,E4,G4')" in result['code']
    assert output_file.exists()


def test_render_music_code_requires_result_variable(monkeypatch):
    monkeypatch.setattr(gemini_service, 'write', lambda *args, **kwargs: None)

    result = gemini_service.render_music_code("chord('C4,E4,G4')")

    assert 'error' in result
    assert 'result' in result['error']


def test_render_code_route_returns_validation_error():
    app = create_app()
    client = app.test_client()

    response = client.post('/render-code', json={})

    assert response.status_code == 400
    assert response.get_json()['error'] == 'No code provided'


def test_revise_route_dispatches_to_revision_service(monkeypatch):
    app = create_app()
    client = app.test_client()

    captured = {}

    def fake_revise_music(user_prompt, generation_config, current_code, current_brief, request_text='', mode='change'):
        captured['user_prompt'] = user_prompt
        captured['generation_config'] = generation_config
        captured['current_code'] = current_code
        captured['current_brief'] = current_brief
        captured['request_text'] = request_text
        captured['mode'] = mode
        return {
            'brief': current_brief,
            'code': 'result = chord(\'D4,F#4,A4\')',
            'midi_url': '/download/midi'
        }

    monkeypatch.setattr('app.routes.api.revise_music', fake_revise_music)

    response = client.post('/revise', json={
        'prompt': 'Make it warmer',
        'config': {'genre': 'Ambient'},
        'brief': 'Current brief',
        'code': "result = chord('C4,E4,G4')",
        'request': 'Soften the lead',
        'mode': 'change'
    })

    assert response.status_code == 200
    assert response.get_json()['midi_url'] == '/download/midi'
    assert captured['user_prompt'] == 'Make it warmer'
    assert captured['generation_config'] == {'genre': 'Ambient'}
    assert captured['current_code'] == "result = chord('C4,E4,G4')"
    assert captured['current_brief'] == 'Current brief'
    assert captured['request_text'] == 'Soften the lead'
    assert captured['mode'] == 'change'


def test_generate_music_handles_gemini_server_errors(monkeypatch):
    class FailingModels:
        def generate_content(self, *args, **kwargs):
            raise RuntimeError('500 INTERNAL')

    class FailingClient:
        models = FailingModels()

    monkeypatch.setattr(gemini_service, 'client', FailingClient())

    result = gemini_service.generate_music('A dark synth melody', {})

    assert 'error' in result
    assert 'Gemini prompt expansion failed' in result['error']
    assert '500 INTERNAL' in result['error']


def test_generate_route_handles_gemini_server_errors(monkeypatch):
    class FailingModels:
        def generate_content(self, *args, **kwargs):
            raise RuntimeError('500 INTERNAL')

    class FailingClient:
        models = FailingModels()

    monkeypatch.setattr(gemini_service, 'client', FailingClient())

    app = create_app()
    client = app.test_client()

    response = client.post('/generate', json={
        'prompt': 'A dark synth melody',
        'config': {}
    })

    assert response.status_code == 500
    payload = response.get_json()
    assert payload is not None
    assert 'Gemini prompt expansion failed' in payload['error']
    assert '500 INTERNAL' in payload['error']
