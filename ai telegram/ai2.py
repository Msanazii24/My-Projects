import os
import sys
import sqlite3
import logging
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from openai import AsyncOpenAI

# =========================
# ENV + LOGGING
# =========================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID") or 0)

logging.basicConfig(
    format="%(asctime)s | %(levelname)5s | %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("xman-ai-stable")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not OWNER_ID:
    log.error("❌ Missing one or more required env vars: TELEGRAM_TOKEN, OPENAI_API_KEY, OWNER_ID")
    sys.exit(1)

# =========================
# SINGLE-INSTANCE LOCK
# =========================
LOCK_FILE = "xman_ai.lock"

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        log.error("❌ Another instance appears to be running (lock file found).")
        log.error("   If you're sure it's not, delete xman_ai.lock and start again.")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass

# =========================
# DB SETUP + SAFE EXEC
# =========================
DB_PATH = "users.db"
_db_lock = threading.Lock()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

@contextmanager
def db_cursor():
    with _db_lock:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

def db_init_and_migrate():
    with db_cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            role TEXT DEFAULT 'basic',
            messages INTEGER DEFAULT 0
        )
        """)
        # Hardening: add columns if missing
        def add_col(name, coldef):
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {name} {coldef}")
            except sqlite3.OperationalError:
                pass  # already exists

        add_col("name", "TEXT")
        add_col("role", "TEXT DEFAULT 'basic'")
        add_col("messages", "INTEGER DEFAULT 0")

def db_get_role(uid: str) -> str:
    with db_cursor() as cur:
        cur.execute("SELECT role FROM users WHERE id=?", (uid,))
        row = cur.fetchone()
        return row["role"] if row and row["role"] else "basic"

def db_add_or_update_user(uid: str, name: str):
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO users (id, name, role, messages) VALUES (?, ?, 'basic', 0)", (uid, name))
        cur.execute("UPDATE users SET name=? WHERE id=?", (name, uid))

def db_increment_messages(uid: str):
    with db_cursor() as cur:
        cur.execute("UPDATE users SET messages = messages + 1 WHERE id=?", (uid,))

def db_set_role(uid: str, role: str):
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO users (id, name, role, messages) VALUES (?, '', ?, 0)", (uid, role))
        cur.execute("UPDATE users SET role=? WHERE id=?", (role, uid))

def db_list_users():
    with db_cursor() as cur:
        cur.execute("SELECT id, name, role, messages FROM users ORDER BY messages DESC")
        return cur.fetchall()

# =========================
# OPENAI CLIENT
# =========================
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# =========================
# GLOBALS
# =========================
conversation_memory = {}   # {user_id: [{"role":"user/assistant","content":...}, ...]}
cooldowns = {}
redeem_codes = {"PREMIUM123": "premium"}  # simple demo

# =========================
# HELPERS
# =========================
def split_message(text: str, limit: int = 4000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def get_name(update: Update) -> str:
    u = update.effective_user
    return (u.first_name or u.username or "there")

def role_cooldown(role: str) -> int:
    return 1 if role == "premium" else 5

def html_welcome(name: str) -> str:
    # Use HTML to avoid Markdown quirks.
    return (
        f"👋 <b>Hello {name}!</b>\n\n"
        f"🤖 Welcome to <b>XMAN AI – Stable v2.1</b>.\n"
        f"I can:\n"
        f"• 💬 Chat & answer anything\n"
        f"• 🎨 Generate images (Premium)\n"
        f"• 🧠 Keep short memory for context\n\n"
        f"💎 Want <b>Premium</b> (faster & more creative)? Tap <i>Contact for Premium</i>.\n"
        f"Or press <i>Done</i> to begin!"
    )

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Start Chat", callback_data="done"),
            InlineKeyboardButton("💎 Contact for Premium", callback_data="contact")
        ],
        [InlineKeyboardButton("❓ Help / How to Use", callback_data="help")]
    ])

async def safe_send_long(update: Update, text: str, **kwargs):
    parts = split_message(text)
    # If there's a "Thinking..." message, better to send new messages for long outputs to avoid edit limits.
    for i, p in enumerate(parts):
        if i == 0:
            await update.message.reply_text(p, **kwargs)
        else:
            await update.message.chat.send_message(p, **kwargs)

# =========================
# ERROR HANDLER
# =========================
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled exception:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Oops, something went wrong. Please try again in a moment."
            )
    except Exception:
        pass

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = get_name(update)
    db_add_or_update_user(uid, name)
    await update.message.reply_text(
        html_welcome(name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    name = query.from_user.first_name or query.from_user.username or "User"

    if query.data == "contact":
        await query.edit_message_text(
            text=(
                f"💎 Hi {name}!\n\n"
                f"To upgrade to <b>Premium</b>, contact the owner:\n"
                f"👉 <a href=\"tg://user?id={OWNER_ID}\">Message Owner</a>\n\n"
                f"Premium unlocks:\n"
                f"• ⚡ Faster, longer replies\n"
                f"• 🎨 Image generation\n"
                f"• 🧠 Better memory\n\n"
                f"Type /start to return to the main menu."
            ),
            parse_mode=ParseMode.HTML
        )

    elif query.data == "done":
        await query.edit_message_text(
            text=f"✅ Awesome, {name}! Type anything to start chatting. I’m ready 🤖"
        )

    elif query.data == "help":
        await query.edit_message_text(
            text=(
                "🧭 <b>How to Use XMAN AI</b>\n\n"
                "• Just send a message to chat.\n"
                "• <b>/img &lt;prompt&gt;</b> — Generate AI image (Premium)\n"
                "• <b>/redeem &lt;code&gt;</b> — Redeem Premium code\n"
                "• <b>/start</b> — Show the welcome menu again\n\n"
                "Owner tools:\n"
                "• <b>/list_users</b> — Show users & usage\n"
            ),
            parse_mode=ParseMode.HTML
        )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    args = context.args or []
    if not args:
        await update.message.reply_text("⚠️ Usage: /redeem <code>")
        return
    code = args[0].strip().upper()
    if code in redeem_codes:
        db_set_role(uid, "premium")
        del redeem_codes[code]
        await update.message.reply_text("✅ Code accepted! You’re now <b>PREMIUM</b> 🎉", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ Invalid or expired code.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_ID:
        await update.message.reply_text("🚫 Owner only.")
        return
    rows = db_list_users()
    if not rows:
        await update.message.reply_text("No users yet.")
        return
    lines = ["👥 <b>User Stats</b>\n"]
    for r in rows:
        lines.append(f"• {r['name'] or 'Unknown'} ({r['id']}) — {r['role']} — {r['messages']} msgs")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def img_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    role = db_get_role(uid)
    if role != "premium":
        await update.message.reply_text("🚫 Only <b>PREMIUM</b> users can use /img.", parse_mode=ParseMode.HTML)
        return
    prompt = " ".join(context.args or [])
    if not prompt:
        await update.message.reply_text("⚠️ Usage: /img <description>")
        return
    await update.message.reply_text("🎨 Generating your image, please wait...")
    try:
        image = await client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
        url = image.data[0].url
        await update.message.reply_photo(url, caption=f"🖼️ {prompt}")
    except Exception as e:
        log.error(f"Image generation error: {e}")
        await update.message.reply_text("❌ Image generation failed. Try again later.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = get_name(update)
    role = db_get_role(uid)

    # First-time users who didn't send /start
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id=?", (uid,))
        if not cur.fetchone():
            db_add_or_update_user(uid, name)
            await update.message.reply_text(
                html_welcome(name), parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard()
            )
            return

    # Cooldown
    now = datetime.now()
    wait = role_cooldown(role)
    until = cooldowns.get(uid)
    if until and now < until:
        await update.message.reply_text("⏳ Please wait a few seconds before your next message.")
        return
    cooldowns[uid] = now + timedelta(seconds=wait)

    user_text = (update.message.text or "").strip()
    if not user_text:
        await update.message.reply_text("🙂 Send me a message and I’ll reply.")
        return

    db_increment_messages(uid)

    await context.bot.send_chat_action(chat_id=uid, action=ChatAction.TYPING)
    thinking = await update.message.reply_text("🤖 Thinking...")

    # Conversation memory (last 10 exchanges)
    history = conversation_memory.get(uid, [])
    history.append({"role": "user", "content": user_text})
    conversation_memory[uid] = history[-10:]

    system_prompt = (
        f"You are XMAN AI (Stable v2.1), a friendly, concise and helpful assistant. "
        f"You are chatting with {name}. Personalize lightly. Use clear, direct language."
    )

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + conversation_memory[uid],
            timeout=60
        )
        reply = resp.choices[0].message.content.strip()
        conversation_memory[uid].append({"role": "assistant", "content": reply})

        # Safer sending (don’t keep editing long messages)
        await thinking.delete()
        await safe_send_long(update, reply)
    except Exception as e:
        log.error(f"OpenAI chat error: {e}")
        try:
            await thinking.edit_text("⚠️ Something went wrong. Please try again.")
        except Exception:
            await update.message.reply_text("⚠️ Something went wrong. Please try again.")

# =========================
# MAIN
# =========================
def main():
    acquire_lock()
    try:
        db_init_and_migrate()

        app = ApplicationBuilder()\
            .token(TELEGRAM_TOKEN)\
            .connect_timeout(30)\
            .read_timeout(30)\
            .build()

        # Commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("redeem", redeem))
        app.add_handler(CommandHandler("img", img_cmd))
        app.add_handler(CommandHandler("list_users", list_users))

        # Buttons
        app.add_handler(CallbackQueryHandler(button_click))

        # Messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

        # Errors
        app.add_error_handler(on_error)

        log.info("🤖 XMAN AI – Stable v2.1 starting…")
        print("✅ Bot is live — type /start in Telegram!")

        # Drop old pending updates to avoid conflicts and stale messages
        app.run_polling(drop_pending_updates=True)
    finally:
        release_lock()

if __name__ == "__main__":
    main()
