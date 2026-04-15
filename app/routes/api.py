import os
import json
import traceback
from flask import Blueprint, request, jsonify, send_file
from app.services.gemini_service import generate_music
from app.services.audio_service import render_midi_to_audio
from app.config import BASE_DIR

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        user_prompt = data.get('prompt', '')
        generation_config = data.get('config', {})
        if not user_prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        result = generate_music(user_prompt, generation_config)
        
        if 'error' in result:
            return jsonify(result), 500
            
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tags', methods=['GET'])
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
    return jsonify(tags)

@api_bp.route('/download/midi', methods=['GET'])
def download_midi():
    midi_path = os.path.join(BASE_DIR, "output.mid")
    return send_file(midi_path, as_attachment=True)

@api_bp.route('/download/audio', methods=['GET'])
def download_audio():
    format = request.args.get('format', 'mp3')
    try:
        audio_stream = render_midi_to_audio("output.mid", format)
        return send_file(audio_stream, mimetype=f'audio/{format}', as_attachment=True, download_name=f"output.{format}")
    except Exception as e:
        return jsonify({'error': str(e)}), 500
