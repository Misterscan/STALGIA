import os
import json
import traceback
from flasgger import swag_from
from flask import Blueprint, request, jsonify, send_file
from pretty_midi.constants import INSTRUMENT_MAP, DRUM_MAP
from app.services.gemini_service import generate_music, render_music_code, revise_music
from app.services.audio_service import render_midi_to_audio
from app.config import BASE_DIR

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate', methods=['POST'])
@swag_from({
    'tags': ['Generation'],
    'description': 'Generates music using LLM prompt based on music theory and configuration.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'example': 'A heroic battle theme'
                    },
                    'config': {
                        'type': 'object',
                        'properties': {
                            'genre': {'type': 'string', 'example': 'Orchestral'},
                            'tempo': {'type': 'string', 'example': '120 BPM'},
                            'key': {'type': 'string', 'example': 'C minor'}
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'A successful generation response',
            'schema': {
                'type': 'object',
                'properties': {
                    'brief': {'type': 'string'},
                    'code': {'type': 'string'},
                    'midi_url': {'type': 'string'}
                }
            }
        },
        '400': {
            'description': 'Bad Request'
        },
        '500': {
            'description': 'Internal Server Error'
        }
    }
})
def generate():
    try:
        data = request.json or {}
        user_prompt = data.get('prompt', '')
        generation_config = data.get('config', {})
        variation_request = data.get('variation_request', '')
        if not user_prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        result = generate_music(user_prompt, generation_config, variation_request=variation_request)
        
        if 'error' in result:
            return jsonify(result), 500
            
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/render-code', methods=['POST'])
@swag_from({
    'tags': ['Generation'],
    'description': 'Executes user-edited musicpy code and regenerates the MIDI output.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {
                        'type': 'string',
                        'example': "result = chord('C4,E4,G4')"
                    },
                    'brief': {
                        'type': 'string'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Updated MIDI generated from user-provided code.'
        },
        '400': {
            'description': 'Bad Request'
        },
        '500': {
            'description': 'Execution failure'
        }
    }
})
def render_code():
    try:
        data = request.json or {}
        music_code = data.get('code', '')
        brief = data.get('brief')

        if not music_code:
            return jsonify({'error': 'No code provided'}), 400

        result = render_music_code(music_code)
        if 'error' in result:
            return jsonify(result), 500

        if brief:
            result['brief'] = brief

        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/revise', methods=['POST'])
@swag_from({
    'tags': ['Generation'],
    'description': 'Asks Gemini to change specifics in the current composition or regenerate a new variation.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string'},
                    'config': {'type': 'object'},
                    'brief': {'type': 'string'},
                    'code': {'type': 'string'},
                    'request': {'type': 'string'},
                    'mode': {
                        'type': 'string',
                        'example': 'change'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'A successful revision or regeneration response'
        },
        '400': {
            'description': 'Bad Request'
        },
        '500': {
            'description': 'Revision failure'
        }
    }
})
def revise():
    try:
        data = request.json or {}
        user_prompt = data.get('prompt', '')
        generation_config = data.get('config', {})
        current_brief = data.get('brief', '')
        current_code = data.get('code', '')
        request_text = data.get('request', '')
        mode = data.get('mode', 'change')

        if not user_prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        if mode != 'regenerate' and not current_code:
            return jsonify({'error': 'No current code provided'}), 400

        result = revise_music(
            user_prompt,
            generation_config,
            current_code,
            current_brief,
            request_text=request_text,
            mode=mode,
        )

        if 'error' in result:
            return jsonify(result), 500

        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tags', methods=['GET'])
@swag_from({
    'tags': ['Data'],
    'description': 'Fetches available tags from the underlying JSON data files.',
    'responses': {
        '200': {
            'description': 'A dictionary specifying all configured parameters.',
            'schema': {
                'type': 'object',
                'example': {
                    'genre': {
                        'Lo-Fi': ['lofi hip hop', 'chillhop'],
                        'Electronic': ['synthwave', 'ambient']
                    }
                }
            }
        }
    }
})
def get_tags():
    # Load from root tags dir
    tags_dir = os.path.join(BASE_DIR, 'tags')
    tags = {}
    if os.path.exists(tags_dir):
        for filename in os.listdir(tags_dir):
            if filename.endswith('.json'):
                key = filename[:-5]
                with open(os.path.join(tags_dir, filename), 'r', encoding='utf-8') as f:
                    try:
                        tags[key] = json.load(f)
                    except json.JSONDecodeError:
                        pass

    # Use pretty_midi's built-in General MIDI maps as the authoritative
    # instrument vocabulary used by the MIDI conversion stack.
    tags['instruments'] = list(INSTRUMENT_MAP) + list(DRUM_MAP)

    return jsonify(tags)

@api_bp.route('/download/midi', methods=['GET'])
@swag_from({
    'tags': ['Downloads'],
    'description': 'Downloads the most recently generated MIDI output.',
    'responses': {
        '200': {
            'description': 'MIDI file binary stream'
        }
    }
})
def download_midi():
    midi_path = os.path.join(BASE_DIR, "output.mid")
    return send_file(midi_path, as_attachment=True)

@api_bp.route('/download/audio', methods=['GET'])
@swag_from({
    'tags': ['Downloads'],
    'description': 'Renders the latest MIDI file directly to audio (e.g. mp3/wav).',
    'parameters': [
        {
            'name': 'format',
            'in': 'query',
            'type': 'string',
            'required': False,
            'default': 'mp3',
            'description': 'Target audio format extension (e.g. mp3, wav, flac)'
        }
    ],
    'responses': {
        '200': {
            'description': 'Audio file binary stream'
        },
        '500': {
            'description': 'Audio rendering error'
        }
    }
})
def download_audio():
    format = request.args.get('format', 'mp3')
    try:
        audio_stream = render_midi_to_audio("output.mid", format)
        return send_file(audio_stream, mimetype=f'audio/{format}', as_attachment=True, download_name=f"output.{format}")
    except Exception as e:
        return jsonify({'error': str(e)}), 500
