# nlp_parser.py
import json
import re
from openai_client import chat_parse

def local_parse(text: str):
    t = text.lower()
    version = None
    m = re.search(r"\b\d\.\d\b", t)
    if m:
        version = m.group(0)
    player_type = "f2p"
    if "welkin+bp" in t or ("welkin" in t and "battle" in t):
        player_type = "welkin+bp"
    elif "welkin" in t:
        player_type = "welkin"
    elif "battle pass" in t or "bp" in t:
        player_type = "welkin+bp"

    include_map = "map" in t or "region" in t or "open world" in t
    include_story = "story" in t or "story quest" in t
    include_character = "character" in t or "character quest" in t or "char quest" in t

    return {
        "version": version,
        "player_type": player_type,
        "include_map": include_map,
        "include_story": include_story,
        "include_character": include_character
    }

def parse_user_text(text: str):
    # ask OpenAI for structured JSON
    ai_resp = chat_parse(text, max_tokens=200)
    # try to extract JSON
    try:
        # The model returns JSON; try to find first brace ...
        start = ai_resp.find("{")
        if start != -1:
            j = ai_resp[start:]
            data = json.loads(j)
            return data
    except Exception:
        pass

    # fallback to local parse
    return local_parse(text)
