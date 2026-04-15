import traceback
import os
from google.genai import types
from musicpy import *
from app.config import client
from app.prompts.prompts import STAGE1_PROMPT, STAGE2_PROMPT, build_generation_prompt

def generate_music(user_prompt, generation_config):
    combined_prompt = build_generation_prompt(user_prompt, generation_config)

    # Stage 1: Expand Prompt
    response1 = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        config=types.GenerateContentConfig(system_instruction=STAGE1_PROMPT, temperature=0.2, thinking_config=types.ThinkingConfig(thinking_level="low")),
        contents=[combined_prompt]
    )
    expanded_brief = response1.text
    print(f"Expanded Brief: {expanded_brief}")

    # Stage 2: Generate Code (with retry/fix logic)
    music_code = ""
    last_error = ""
    for attempt in range(2): # 1 initial + 1 retry
        prompt = expanded_brief if attempt == 0 else f"The following musicpy code failed with error: {last_error}. Please fix it and return the full corrected code.\n\nCode:\n{music_code}"
        
        response2 = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            config=types.GenerateContentConfig(system_instruction=STAGE2_PROMPT, temperature=0.3, thinking_config=types.ThinkingConfig(thinking_level="low")),
            contents=[prompt]
        )
        music_code = response2.text.strip()
        # Clean markdown if present
        if music_code.startswith("```python"):
            music_code = music_code.split("```python")[1].split("```")[0].strip()
        elif music_code.startswith("```"):
            music_code = music_code.split("```")[1].split("```")[0].strip()
        
        print(f"Attempt {attempt + 1} Generated Code:\n{music_code}")

        try:
            # Execute Code
            exec_globals = {}
            exec("from musicpy import *", exec_globals)
            exec(music_code, exec_globals)
            
            result_obj = exec_globals.get('result')
            if not result_obj:
                 raise ValueError('AI failed to generate a "result" variable')

            # Robust Type Handling for musicpy objects
            if isinstance(result_obj, scale):
                result_obj = chord(result_obj.notes)
            
            # Generate MIDI
            midi_filename = "output.mid" # Output to project root assuming running app.py from root
            write(result_obj, name=midi_filename)
            
            return {
                'brief': expanded_brief,
                'code': music_code,
                'midi_url': '/download/midi'
            }

        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 1:
                return {
                    'error': f"Failed after 2 attempts. Last error: {last_error}", 
                    'code': music_code
                }

    return {'error': "Unknown error occurred"}
