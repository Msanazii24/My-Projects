# openai_client.py
import os
from typing import Dict, Any
from config import OPENAI_API_KEY, OPENAI_MODEL

try:
    # modern usage: from openai import OpenAI
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    # fallback to older openai package if needed
    import openai
    openai.api_key = OPENAI_API_KEY
    client = None

def chat_parse(prompt: str, max_tokens: int = 400) -> str:
    """
    Send a small prompt to OpenAI to parse user intent or give a smart estimate.
    Returns the assistant text (string). Errors return a fallback string.
    """
    system = (
        "You are a concise assistant that parses user requests for a Genshin "
        "primogem calculator. Return a JSON object with keys: version, player_type, include_map (bool), include_story (bool), include_character (bool)."
    )
    user_msg = f"User input: {prompt}\n\nReturn only valid JSON."

    try:
        if client is not None:
            resp = client.responses.create(
                model=OPENAI_MODEL,
                input=[{"role":"system","content":system},{"role":"user","content":user_msg}],
                max_tokens=max_tokens
            )
            # response.output_text is a convenience field in new client
            text = resp.output_text if hasattr(resp, "output_text") else str(resp)
            return text
        else:
            # fallback to older openai.ChatCompletion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"system", "content":system}, {"role":"user","content":user_msg}],
                max_tokens=max_tokens,
                temperature=0
            )
            return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f'{{"error":"openai error - {e}"}}'
