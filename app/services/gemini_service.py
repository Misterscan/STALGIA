import traceback
import os
from google.genai import types
from musicpy import *
from app.config import client
from app.prompts.prompts import STAGE1_PROMPT, STAGE2_PROMPT, build_generation_prompt
from app.examples.prepackaged import PREPACKAGED_EXAMPLES

def _clean_generated_code(raw_code):
    music_code = (raw_code or '').strip()
    if music_code.startswith("```python"):
        return music_code.split("```python", 1)[1].split("```", 1)[0].strip()
    if music_code.startswith("```"):
        return music_code.split("```", 1)[1].split("```", 1)[0].strip()
    return music_code


def _execute_music_code(music_code, midi_filename="output.mid"):
    exec_globals = {}
    exec("from musicpy import *", exec_globals)
    exec(music_code, exec_globals)

    result_obj = exec_globals.get('result')
    if result_obj is None:
        raise ValueError('Code must define a "result" variable')

    if isinstance(result_obj, scale):
        result_obj = chord(result_obj.notes)

    write(result_obj, name=midi_filename)


def _request_gemini_text(prompt, system_instruction, model, temperature, thinking_level):
    response = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
        ),
        contents=[prompt]
    )

    response_text = getattr(response, 'text', None)
    if not response_text:
        raise ValueError(f'Gemini returned an empty response for model {model}')

    return response_text


def _expand_prompt_with_retries(combined_prompt):
    last_error = ''

    for _ in range(3):
        try:
            expanded_brief = _request_gemini_text(
                combined_prompt,
                STAGE1_PROMPT,
                'gemini-3.1-flash-lite-preview',
                0.2,
                'low',
            )
            print(f"Expanded Brief: {expanded_brief}")
            return {'brief': expanded_brief}
        except Exception as e:
            last_error = str(e)
            traceback.print_exc()

    return {'error': f'Gemini prompt expansion failed after 3 attempts. Last error: {last_error}'}


def _generate_code_with_retries(initial_prompt, retry_prefix, initial_model='gemini-3.1-pro-preview'):
    if not client:
        return {'error': 'GEMINI_API_KEY is not configured'}

    music_code = ""
    last_error = ""

    for attempt in range(3):
        prompt = (
            initial_prompt
            if attempt == 0
            else f"{retry_prefix}\n\nThe following musicpy code failed with error: {last_error}. Please fix it and return the full corrected code.\n\nCode:\n{music_code}"
        )

        current_model = initial_model if attempt == 0 else 'gemini-3.1-flash-lite-preview'
        current_temp = 0.3 if attempt == 0 else 0.1
        current_thinking_level = 'low' if attempt == 0 else 'minimal'

        try:
            response_text = _request_gemini_text(
                prompt,
                STAGE2_PROMPT,
                current_model,
                current_temp,
                current_thinking_level,
            )
        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 2:
                return {
                    'error': f'Gemini code generation failed after 3 attempts. Last error: {last_error}',
                    'code': music_code,
                }
            continue

        music_code = _clean_generated_code(response_text)
        print(f"Attempt {attempt + 1} Generated Code:\n{music_code}")

        try:
            _execute_music_code(music_code)
            return {'code': music_code, 'midi_url': '/download/midi'}
        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 2:
                return {
                    'error': f"Failed after 3 attempts. Last error: {last_error}",
                    'code': music_code,
                }

    return {'error': 'Unknown error occurred'}


def render_music_code(music_code):
    cleaned_code = _clean_generated_code(music_code)
    if not cleaned_code:
        return {'error': 'No code provided'}

    try:
        _execute_music_code(cleaned_code)
        return {
            'code': cleaned_code,
            'midi_url': '/download/midi',
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'error': str(e),
            'code': cleaned_code,
        }


def _generate_music_variation(user_prompt, generation_config, variation_request=''):
    combined_prompt = build_generation_prompt(user_prompt, generation_config)
    if variation_request:
        combined_prompt += (
            "\n\nVariation request:\n"
            f"{variation_request}\n\n"
            "This must be treated as a request for a fresh variation, not a small patch."
        )

    if not client:
        return {'error': 'GEMINI_API_KEY is not configured'}

    expansion_result = _expand_prompt_with_retries(combined_prompt)
    if 'error' in expansion_result:
        return expansion_result
    expanded_brief = expansion_result['brief']

    generation_result = _generate_code_with_retries(
        expanded_brief,
        "Please repair the code while keeping the brief intact.",
    )
    if 'error' in generation_result:
        return generation_result

    return {
        'brief': expanded_brief,
        'code': generation_result['code'],
        'midi_url': generation_result['midi_url'],
    }


def generate_music(user_prompt, generation_config, variation_request=''):
    # Short-circuit check for pre-packaged verified scripts
    exact_match = user_prompt.strip()
    if exact_match in PREPACKAGED_EXAMPLES:
        example_data = PREPACKAGED_EXAMPLES[exact_match]
        expanded_brief = example_data["brief"]
        music_code = example_data["code"]
        
        try:
            _execute_music_code(music_code)
            
            return {
                'brief': expanded_brief,
                'code': music_code,
                'midi_url': '/download/midi'
            }
        except Exception as e:
            traceback.print_exc()
            return {'error': f"Pre-packaged execution failed: {str(e)}", 'code': music_code}

    if variation_request:
        return _generate_music_variation(user_prompt, generation_config, variation_request=variation_request)

    if not client:
        return {'error': 'GEMINI_API_KEY is not configured'}

    combined_prompt = build_generation_prompt(user_prompt, generation_config)

    try:
        response1 = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            config=types.GenerateContentConfig(
                system_instruction=STAGE1_PROMPT,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_level="low")
            ),
            contents=[combined_prompt]
        )
        expanded_brief = response1.text
        print(f"Expanded Brief: {expanded_brief}")
    except Exception as e:
        traceback.print_exc()
        return {'error': f'Gemini prompt expansion failed: {str(e)}'}

    music_code = ""
    last_error = ""
    for attempt in range(3):
        prompt = expanded_brief if attempt == 0 else f"The following musicpy code failed with error: {last_error}. Please fix it and return the full corrected code.\n\nCode:\n{music_code}"

        current_model = 'gemini-3.1-pro-preview' if attempt == 0 else 'gemini-3.1-flash-lite-preview'
        current_temp = 0.3 if attempt == 0 else 0.1
        current_thinking_config = types.ThinkingConfig(thinking_level="low") if attempt == 0 else types.ThinkingConfig(thinking_level="minimal")

        try:
            response2 = client.models.generate_content(
                model=current_model,
                config=types.GenerateContentConfig(
                    system_instruction=STAGE2_PROMPT,
                    temperature=current_temp,
                    thinking_config=current_thinking_config
                ),
                contents=[prompt]
            )
        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 2:
                return {
                    'error': f'Gemini code generation failed: {last_error}',
                    'code': music_code
                }
            continue

        music_code = _clean_generated_code(response2.text)
        print(f"Attempt {attempt + 1} Generated Code:\n{music_code}")

        try:
            _execute_music_code(music_code)
            return {
                'brief': expanded_brief,
                'code': music_code,
                'midi_url': '/download/midi'
            }
        except Exception as e:
            last_error = str(e)
            traceback.print_exc()
            if attempt == 2:
                return {
                    'error': f"Failed after 3 attempts. Last error: {last_error}",
                    'code': music_code
                }

    return {'error': "Unknown error occurred"}


def revise_music(user_prompt, generation_config, current_code, current_brief, request_text='', mode='change'):
    normalized_mode = (mode or 'change').strip().lower()
    if normalized_mode == 'regenerate':
        variation_request = request_text or 'Generate a fresh variation with a noticeably different melody.'
        return generate_music(user_prompt, generation_config, variation_request=variation_request)

    if not client:
        return {'error': 'GEMINI_API_KEY is not configured'}

    cleaned_code = _clean_generated_code(current_code)
    if not cleaned_code:
        return {'error': 'No existing code provided'}

    prompt = (
        "Revise the current musicpy composition according to the user request.\n\n"
        f"Original user prompt:\n{user_prompt or 'N/A'}\n\n"
        f"Configuration:\n{generation_config or {}}\n\n"
        f"Current musical brief:\n{current_brief or 'N/A'}\n\n"
        f"User change request:\n{request_text or 'Improve the composition while preserving its identity.'}\n\n"
        "Requirements:\n"
        "- Return full replacement musicpy code only.\n"
        "- Preserve the overall song identity unless the user explicitly asks to replace it.\n"
        "- Change melody, harmony, instrumentation, arrangement, or rhythm only as needed to satisfy the request.\n"
        "- Keep the final code executable and continue defining result.\n\n"
        f"Current code:\n{cleaned_code}"
    )

    revision_result = _generate_code_with_retries(
        prompt,
        "Please repair the revised code and keep the requested musical changes.",
        initial_model='gemini-3.1-flash-lite-preview',
    )
    if 'error' in revision_result:
        return revision_result

    return {
        'brief': current_brief,
        'code': revision_result['code'],
        'midi_url': revision_result['midi_url'],
    }
