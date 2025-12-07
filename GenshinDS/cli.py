# cli.py
from nlp_parser import parse_user_text
from calculator import calculate_for_patch

def run_cli():
    print("Genshin Primo AI — CLI")
    text = input("Describe what you want (e.g. '6.3 welkin new map'): ")
    parsed = parse_user_text(text)
    version = parsed.get("version") or input("Which patch? (e.g. 6.3): ")
    player = parsed.get("player_type", "f2p")
    result = calculate_for_patch(version, player_type=player,
                                 include_story=parsed.get("include_story", True),
                                 include_character=parsed.get("include_character", True),
                                 include_map=parsed.get("include_map", False))
    print("\n--- Result ---")
    print(f"Patch: {result['patch']} ({result['patch_date']})")
    for k, v in result["details"].items():
        print(f"{k}: {v}")
    print("----------------")
    print("TOTAL:", result["total"])

if __name__ == "__main__":
    run_cli()
