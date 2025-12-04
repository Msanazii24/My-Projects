import os
import sqlite3
import logging
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from openai import AsyncOpenAI
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT DEFAULT 'basic'
)
""")
conn.commit()

def get_role(user_id):
    cur.execute("SELECT role FROM users WHERE id=?", (user_id,))
    res = cur.fetchone()
    return res[0] if res else "basic"

def set_role(user_id, role):
    cur.execute("INSERT OR REPLACE INTO users (id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()

# ---------------- GLOBALS ----------------
conversation_memory = {}
cooldowns = {}
redeem_codes = {"PREMIUM123": "premium"}

def split_message(text, limit=4000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def is_owner(user_id):
    return user_id == OWNER_ID

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    name = user.first_name or user.username or "there"
    role = get_role(user_id)

    # Save or update user
    cur.execute("INSERT OR IGNORE INTO users (id, name, role) VALUES (?, ?, ?)", (user_id, name, role))
    cur.execute("UPDATE users SET name=? WHERE id=?", (name, user_id))
    conn.commit()

    # Welcome text
    welcome_text = (
        f"👋 **Hello {name}!**\n\n"
        f"🤖 Welcome to **XMAN AI Assistant** — a smart combo of multiple AIs that can:\n"
        f"💬 Chat & answer questions\n"
        f"🎨 Generate images\n"
        f"🧠 Learn your style over time\n\n"
        f"💎 Want **PREMIUM** features (faster responses, more creativity)?\n"
        f"Press *Contact for Premium* below.\n\n"
        f"Or just press *Done* to begin!"
    )

    buttons = [
        [
            InlineKeyboardButton("💬 Contact for Premium", callback_data="contact"),
            InlineKeyboardButton("✅ Done", callback_data="done")
        ],
        [InlineKeyboardButton("❓ Help / How to Use", callback_data="help")]
    ]

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- BUTTON HANDLER ----------------
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = str(user.id)
    name = user.first_name or user.username or "User"
    await query.answer()

    if query.data == "contact":
        await query.edit_message_text(
            f"💎 Hey {name}!\n\n"
            f"If you'd like to upgrade to **PREMIUM**, please contact the bot owner:\n"
            f"👉 [Message Owner](tg://user?id={OWNER_ID})\n\n"
            f"They'll guide you through the process.\n\n"
            f"Once upgraded, you'll unlock:\n"
            f"✨ Faster AI responses\n"
            f"🎨 Image generation\n"
            f"📚 Conversation memory\n\n"
            f"Press /start again to return to the main menu.",
            parse_mode="Markdown"
        )

    elif query.data == "done":
        await query.edit_message_text(
            f"✅ Awesome, {name}!\n\n"
            f"You can now start chatting. Just type anything — I’ll reply instantly 🤖"
        )

    elif query.data == "help":
        help_text = (
            f"❓ **How to Use XMAN AI**\n\n"
            f"💬 *Chat with AI*: Just send a message or question.\n"
            f"🎨 *Create Images*: Use `/img <description>` (Premium only)\n"
            f"💎 *Upgrade*: Tap *Contact for Premium* on the main menu.\n\n"
            f"⚙️ Commands:\n"
            f"/start — Show main menu\n"
            f"/redeem <code> — Redeem premium code\n"
            f"/img <text> — Generate AI image (Premium)\n"
            f"/manage — Owner panel\n\n"
            f"Ready? Press /start to go back! 🚀"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown")

# ---------------- CHAT ----------------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    user_name = user.first_name or user.username or "User"
    role = get_role(user_id)
    user_input = update.message.text.strip()
    now = datetime.now()

    # Auto welcome for new users
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cur.fetchone():
        await start(update, context)
        return

    # Rate limit
    cooldown_time = 5 if role == "basic" else 1
    if user_id in cooldowns and now < cooldowns[user_id]:
        await update.message.reply_text("⏳ Please wait a few seconds before sending another message.")
        return
    cooldowns[user_id] = now + timedelta(seconds=cooldown_time)

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    thinking_msg = await update.message.reply_text("🤖 Thinking...")

    history = conversation_memory.get(user_id, [])
    history.append({"role": "user", "content": user_input})
    conversation_memory[user_id] = history[-10:]

    system_prompt = (
        f"You are a friendly and intelligent AI assistant chatting with {user_name}. "
        f"You belong to a multi-AI system called XMAN AI. "
        "Address them naturally by name when appropriate. "
        "Give detailed, creative answers for premium users, "
        "and short, clear answers for basic users."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + conversation_memory[user_id]
        )
        reply = response.choices[0].message.content.strip()
        conversation_memory[user_id].append({"role": "assistant", "content": reply})

        for part in split_message(reply):
            await thinking_msg.edit_text(part)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await thinking_msg.edit_text("⚠️ Oops! Something went wrong. Please try again later.")

# ---------------- IMAGE ----------------
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    role = get_role(user_id)
    prompt = " ".join(context.args)
    if role != "premium":
        await update.message.reply_text("🚫 Only PREMIUM users can use /img.")
        return
    if not prompt:
        await update.message.reply_text("⚠️ Usage: /img <description>")
        return

    await update.message.reply_text("🎨 Generating your image, please wait...")
    try:
        image = await client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
        image_url = image.data[0].url
        await update.message.reply_photo(image_url, caption=f"🖼️ Prompt: {prompt}")
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await update.message.reply_text("❌ Image generation failed. Try again later.")

# ---------------- OWNER COMMANDS ----------------
async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_chat.id):
        await update.message.reply_text("🚫 Only the owner can use this command.")
        return
    await update.message.reply_text(
        "👑 Owner Panel\n\n"
        "/list_users - View all users and roles\n"
        "/add_code <CODE> - Create new premium code"
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_chat.id):
        return
    cur.execute("SELECT id, name, role FROM users")
    users = cur.fetchall()
    msg = "📜 User Roles:\n\n" + "\n".join([f"👤 {u[1]} ({u[0]}) → {u[2]}" for u in users]) if users else "No users yet."
    await update.message.reply_text(msg)

async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_chat.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usage: /add_code <CODE>")
        return
    code = args[0].upper()
    redeem_codes[code] = "premium"
    await update.message.reply_text(f"✅ Added new premium code: {code}")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).connect_timeout(30).read_timeout(30).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", add_code))
    app.add_handler(CommandHandler("img", generate_image))
    app.add_handler(CommandHandler("manage", manage))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("add_code", add_code))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("🤖 Bot running (v1.4) with improved menu and auto-welcome")
    print("✅ Bot started successfully — Try typing /start in Telegram!")
    app.run_polling()

if __name__ == "__main__":
    main()
