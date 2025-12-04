import os
import sys
import sqlite3
import logging
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
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OWNER_ID         = int(os.getenv("OWNER_ID") or 0)
OPENAI_MODEL     = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("xman-ai-clean-v3")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not OWNER_ID:
    log.error("❌ Missing env vars: TELEGRAM_TOKEN, OPENAI_API_KEY, OWNER_ID")
    sys.exit(1)

# =========================
# SINGLE-INSTANCE LOCK
# =========================
LOCK_FILE = "xman_ai.lock"
def acquire_lock():
    if os.path.exists(LOCK_FILE):
        log.error("❌ Another instance is running (lock file exists). Delete xman_ai.lock if stale.")
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
# DB SETUP + MIGRATIONS
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
                messages INTEGER DEFAULT 0,
                last_seen TEXT
            )
        """)
        # Add missing columns safely
        def add_col(col, ddl):
            try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
            except sqlite3.OperationalError: pass
        add_col("name", "TEXT")
        add_col("role", "TEXT DEFAULT 'basic'")
        add_col("messages", "INTEGER DEFAULT 0")
        add_col("last_seen", "TEXT")

def db_upsert_user(uid: str, name: str):
    now = datetime.utcnow().isoformat()
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO users (id, name, role, messages, last_seen) VALUES (?, ?, 'basic', 0, ?)", (uid, name, now))
        cur.execute("UPDATE users SET name=?, last_seen=? WHERE id=?", (name, now, uid))

def db_get_role(uid: str) -> str:
    with db_cursor() as cur:
        cur.execute("SELECT role FROM users WHERE id=?", (uid,))
        row = cur.fetchone()
        return row["role"] if row and row["role"] else "basic"

def db_set_role(uid: str, role: str):
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO users (id, name, role, messages, last_seen) VALUES (?, '', ?, 0, ?)",
                    (uid, role, datetime.utcnow().isoformat()))
        cur.execute("UPDATE users SET role=? WHERE id=?", (role, uid))

def db_inc_messages(uid: str):
    with db_cursor() as cur:
        cur.execute("UPDATE users SET messages = messages + 1 WHERE id=?", (uid,))

def db_list_users():
    with db_cursor() as cur:
        cur.execute("SELECT id, name, role, messages, last_seen FROM users ORDER BY messages DESC")
        return cur.fetchall()

# =========================
# OPENAI
# =========================
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# =========================
# STATE / MEMORY
# =========================
conversation_memory = {}  # {uid: [{"role": "...", "content": "..."}, ...] (last 8)}
cooldowns = {}            # {uid: datetime}
anti_repeat = {}          # {uid: {"last_text": str, "last_at": datetime, "last_reply": str}}
redeem_codes = {"PREMIUM123": "premium"}  # demo

def role_cooldown(role: str) -> int:
    return 1 if role == "premium" else 3

def split_message(text: str, limit: int = 4000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def uname(update: Update) -> str:
    u = update.effective_user
    return (u.first_name or u.username or "friend")

# =========================
# UI STRINGS
# =========================
def welcome_html(name: str) -> str:
    return (
        f"👋 <b>Hello {name}!</b>\n\n"
        f"🤖 Welcome to <b>XMAN AI – Clean v3</b>.\n"
        f"I can:\n"
        f"• 💬 Chat & answer anything\n"
        f"• 🎨 Generate images (Premium)\n"
        f"• 🧠 Keep short memory for context\n\n"
        f"💎 Want <b>Premium</b> (faster & more creative)? Tap <i>Contact for Premium</i>.\n"
        f"Or press <i>Start Chat</i> to begin!"
    )

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Start Chat", callback_data="done"),
            InlineKeyboardButton("💎 Contact for Premium", callback_data="contact"),
        ],
        [InlineKeyboardButton("❓ Help / Commands", callback_data="help")]
    ])

HELP_HTML = (
    "🧭 <b>How to Use XMAN AI</b>\n\n"
    "• Send a message to chat.\n"
    "• <b>/img &lt;prompt&gt;</b> — Generate AI image (Premium)\n"
    "• <b>/redeem &lt;code&gt;</b> — Redeem Premium code\n"
    "• <b>/start</b> — Show the welcome menu\n\n"
    "<i>Owner</i>:\n"
    "• <b>/list_users</b> — show users\n"
    "• <b>/add_code CODE</b> — add a premium code\n"
)

# =========================
# ERROR HANDLER
# =========================
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled exception:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(update.effective_chat.id, "⚠️ Oops, something went wrong. Please try again.")
    except Exception:
        pass

# =========================
# WELCOME / MENU
# =========================
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = uname(update)
    await update.message.reply_text(
        welcome_html(name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_kb()
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db_upsert_user(uid, uname(update))
    await send_welcome(update, context)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    name = q.from_user.first_name or q.from_user.username or "friend"

    if q.data == "contact":
        await q.edit_message_text(
            text=(
                f"💎 Hi {name}!\n\n"
                f"To upgrade to <b>Premium</b>, contact the owner:\n"
                f"👉 <a href=\"tg://user?id={OWNER_ID}\">Message Owner</a>\n\n"
                f"Premium unlocks:\n"
                f"• ⚡ Faster & longer replies\n"
                f"• 🎨 Image generation\n"
                f"• 🧠 Better memory\n\n"
                f"Type /start to return to the main menu."
            ),
            parse_mode=ParseMode.HTML
        )
    elif q.data == "done":
        await q.edit_message_text(f"✅ Great, {name}! Type anything to start chatting with me 🤖")
    elif q.data == "help":
        await q.edit_message_text(HELP_HTML, parse_mode=ParseMode.HTML)

# =========================
# COMMANDS
# =========================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_HTML, parse_mode=ParseMode.HTML)

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

async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_ID:
        await update.message.reply_text("🚫 Owner only.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("⚠️ Usage: /add_code CODE")
        return
    redeem_codes[args[0].strip().upper()] = "premium"
    await update.message.reply_text(f"✅ Added premium code: <b>{args[0].strip().upper()}</b>", parse_mode=ParseMode.HTML)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_ID:
        await update.message.reply_text("🚫 Owner only.")
        return
    rows = db_list_users()
    if not rows:
        await update.message.reply_text("No users yet.")
        return
    lines = ["👥 <b>User Stats</b>"]
    for r in rows:
        lines.append(f"• {r['name'] or 'Unknown'} ({r['id']}) — {r['role']} — {r['messages']} msgs")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def img_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_chat.id)
    role = db_get_role(uid)
    if role != "premium":
        await update.message.reply_text("🚫 Only <b>PREMIUM</b> users can use /img.", parse_mode=ParseMode.HTML)
        return
    prompt = " ".join(context.args or [])
    if not prompt:
        await update.message.reply_text("⚠️ Usage: /img <description>")
        return
    await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
    try:
        image = await client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
        url = image.data[0].url
        await update.message.reply_photo(url, caption=f"🖼️ {prompt}")
    except Exception as e:
        log.error(f"Image gen error: {e}")
        await update.message.reply_text("❌ Image generation failed. Try again later.")

# =========================
# CHAT
# =========================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = str(update.effective_user.id)
    name  = uname(update)
    text  = (update.message.text or "").strip()
    role  = db_get_role(uid)

    # First contact without /start -> show welcome once
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id=?", (uid,))
        if not cur.fetchone():
            db_upsert_user(uid, name)
            await send_welcome(update, context)
            return
        else:
            db_upsert_user(uid, name)

    # Debounce: ignore exact same text within 2 seconds
    now = datetime.utcnow()
    ant = anti_repeat.get(uid, {"last_text": None, "last_at": datetime.utcfromtimestamp(0), "last_reply": None})
    if text and ant["last_text"] == text and (now - ant["last_at"]).total_seconds() < 2:
        return

    # Short cooldown per role
    cd = role_cooldown(role)
    if uid in cooldowns and now < cooldowns[uid]:
        await update.message.reply_text("⏳ One moment, please…")
        return
    cooldowns[uid] = now + timedelta(seconds=cd)

    # Typing indication, but no placeholder message (reduces perceived lag)
    await context.bot.send_chat_action(chat_id=uid, action=ChatAction.TYPING)

    # Memory (last 8 turns)
    hist = conversation_memory.get(uid, [])
    hist.append({"role": "user", "content": text})
    conversation_memory[uid] = hist[-8:]

    system_prompt = (
        f"You are XMAN AI – Clean v3. Be friendly, concise and helpful. "
        f"You are chatting with {name}. Personalize lightly. No overlong preambles."
    )

    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":system_prompt}] + conversation_memory[uid],
            timeout=30
        )
        reply = (resp.choices[0].message.content or "").strip()
        if not reply:
            reply = "I’m here and ready—could you rephrase that?"

        # Avoid repeating identical assistant output back-to-back
        if ant.get("last_reply") and ant["last_reply"] == reply:
            reply += "\n\n(added a tiny change to avoid repetition)"

        conversation_memory[uid].append({"role":"assistant","content":reply})
        db_inc_messages(uid)

        # Send split if long
        for part in split_message(reply):
            await update.message.reply_text(part)
        anti_repeat[uid] = {"last_text": text, "last_at": now, "last_reply": reply}

    except Exception as e:
        log.error(f"OpenAI chat error: {e}")
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
            .connect_timeout(25)\
            .read_timeout(25)\
            .build()

        # Commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("redeem", redeem))
        app.add_handler(CommandHandler("add_code", add_code))
        app.add_handler(CommandHandler("list_users", list_users))
        app.add_handler(CommandHandler("img", img_cmd))

        # Buttons
        app.add_handler(CallbackQueryHandler(button_click))

        # Chat
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

        # Errors
        app.add_error_handler(on_error)

        log.info("🤖 XMAN AI – Clean v3 starting…")
        print("✅ Bot is live — type /start in Telegram!")

        # Drop pending updates to reduce “long loading” backlog effect
        app.run_polling(drop_pending_updates=True)

    finally:
        release_lock()

if __name__ == "__main__":
    main()
