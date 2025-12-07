# calculator.py
import json
import datetime
from typing import Dict, Any

with open("genshin_db.json", "r", encoding="utf-8") as f:
    DB = json.load(f)

D = DB["defaults"]

def days_between(start_date_str: str, days: int):
    start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end = start + datetime.timedelta(days=days)
    return start, end

def calculate_for_patch(patch: str, player_type: str = "f2p",
                        include_story=True, include_character=True, include_map=False) -> Dict[str, Any]:

    # patch existence check
    patch_dates = DB["patches"]
    if patch not in patch_dates:
        # allow user to still compute with defaults
        patch_date = datetime.date.today().isoformat()
    else:
        patch_date = patch_dates[patch]

    total = 0
    details = {}

    # dailies: default 42 days per patch
    dailies_total = D["daily_per_day"] * D["patch_length_days"]
    total += dailies_total
    details["dailies"] = dailies_total

    # welkin / battle pass
    if player_type == "welkin":
        w = D["welkin_daily"] * D["patch_length_days"] + D["welkin_bonus"]
        total += w
        details["welkin"] = w
    elif player_type == "welkin+bp":
        w = D["welkin_daily"] * D["patch_length_days"] + D["welkin_bonus"]
        bp = D["battle_pass"]
        total += w + bp
        details["welkin"] = w
        details["battle_pass"] = bp

    # abyss
    total += D["abyss_reset"]
    details["abyss"] = D["abyss_reset"]

    # imaginary theater
    total += D["imaginary"]
    details["imaginarium"] = D["imaginary"]

    # new mod 450
    total += D["new_mod"]
    details["new_mod"] = D["new_mod"]

    # monthly reset
    total += D["monthly_reset"]
    details["monthly_reset"] = D["monthly_reset"]

    # story
    if include_story:
        total += D["story_quest"]
        details["story_quest"] = D["story_quest"]

    # character
    if include_character:
        total += D["character_quest"]
        details["character_quest"] = D["character_quest"]

    # map
    if include_map:
        total += D["new_map_bonus"]
        details["new_map_bonus"] = D["new_map_bonus"]

    return {"patch": patch, "patch_date": patch_date, "total": total, "details": details}
