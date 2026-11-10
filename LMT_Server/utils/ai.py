import os
import requests
import json
from .db import config

def generate_scene(script_context, character, user_action=None, chat_history=None):
    provider = os.getenv('AI_PROVIDER', 'gemini').lower()
    defaults = {'openai': ('https://api.openai.com/v1', 'gpt-4o-mini'), 'deepseek': ('https://api.deepseek.com/v1', 'deepseek-chat'), 'qwen': ('https://dashscope.aliyuncs.com/compatible-mode/v1', 'qwen-plus'), 'gemini': ('https://generativelanguage.googleapis.com/v1beta', 'gemini-2.5-flash')}
    base, default_model = defaults.get(provider, ('', ''))
    base = os.getenv('AI_BASE_URL', base).rstrip('/')
    api_key = os.getenv(provider.upper() + '_API_KEY') or os.getenv('AI_API_KEY', '')
    model = os.getenv('AI_MODEL', default_model)

    system_prompt = f"""
    You are the Game Master for an AI-driven rule of law education "Juben Sha" (Murder Mystery / RPG).
    The user is playing the character: {character}.
    Script Context: {script_context}

    Your goal is to present a scene, react to the user's previous action (if any), generate dialogues for the OTHER non-player characters (NPCs) in the scene, and provide choices.
    Crucially, you must evaluate if the user's actions have reached a logical conclusion for this scenario (e.g. the truth is found, the law is applied, or the situation is otherwise resolved). If so, set 'is_ended' to true and generate a comprehensive 'end_report'. The end_report should explain which laws were potentially violated in the scenario, how they apply to the user's choices, and what should be done in the future according to the rule of law. If the scenario is not yet resolved, set 'is_ended' to false and 'end_report' to null.

    Respond STRICTLY in JSON format with the following structure:
    {{
        "narrator_text": "The description of the current scene, actions, or environment.",
        "npc_dialogues": [
            {{"name": "NPC Name", "text": "Their spoken dialogue"}}
        ],
        "choices": [
            "Choice 1 description",
            "Choice 2 description"
        ],
        "is_ended": false,
        "end_report": null
    }}
    Do not use markdown formatting around the JSON block. Just output the raw JSON.
    """

    user_prompt = "Start the game." if not user_action else f"User Action: {user_action}"

    payload = {
        "contents": [{"parts":[{"text": user_prompt}]}],
        "systemInstruction": {"parts":[{"text": system_prompt}]}
    }

    try:
        if not api_key or not base or not model:
            raise ValueError('Missing AI configuration')
        if provider == 'gemini':
            response = requests.post(f'{base}/models/{model}:generateContent', headers={'x-goog-api-key': api_key}, json=payload, timeout=90)
            response.raise_for_status()
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            response = requests.post(f'{base}/chat/completions', headers={'Authorization': f'Bearer {api_key}'}, json={'model': model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]}, timeout=90)
            response.raise_for_status()
            text = response.json()['choices'][0]['message']['content']
        text = text.strip()
        # Remove potential markdown formatting from Gemini response
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]

        return json.loads(text.strip())
    except Exception as e:
        error_str = str(e)
        print("AI request failed:", type(e).__name__)

        if "429" in error_str or "Too Many Requests" in error_str:
            narrator_text = "API_KEY额度已花完，继续演绎需联系开发者充值"
            api_err = True
        else:
            narrator_text = "AI 接口调用失败，请检查服务配置后重试。"
            api_err = False

        return {
            "narrator_text": narrator_text,
            "npc_dialogues": [],
            "choices": ["重试", "等待"] if not api_err else [],
            "is_ended": False,
            "api_error": api_err,
            "end_report": None
        }
