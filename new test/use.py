import requests
import json
import time

API_KEY = "1d5c254b44msh2bc046a3057a897p166f14jsn84d319de6407"  # <- replace this
API_HOST = "breachdirectory.p.rapidapi.com"

INPUT_FILE = "emails.txt"
OUTPUT_FILE = "breach_results.txt"


def check_email(email):
    url = "https://breachdirectory.p.rapidapi.com/"
    params = {"func": "auto", "term": email}

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


print("Starting checks…")

with open(INPUT_FILE, "r") as f:
    emails = [line.strip() for line in f if line.strip()]

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for email in emails:
        print(f"Checking: {email}")

        data = check_email(email)

        out.write("=" * 60 + "\n")
        out.write(f"Email: {email}\n")
        out.write("=" * 60 + "\n")

        if "error" in data:
            out.write("ERROR: " + data["error"] + "\n\n")
        elif "result" in data and data["result"]:
            out.write("STATUS: COMPROMISED\n")
            out.write(json.dumps(data, indent=4))
            out.write("\n\n")
        else:
            out.write("STATUS: SAFE (No breaches found)\n\n")

        time.sleep(1)  # avoid rate limits

print(f"Done! Results saved in {OUTPUT_FILE}")
