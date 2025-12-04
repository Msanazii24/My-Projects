import os
import random
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from openai import AsyncOpenAI

# ======================
# CONFIG
# ======================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID") or 0)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("xman-pro-v3")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
client = AsyncOpenAI(api_key=OPENAI_KEY)

# ======================
# MEMORY
# ======================
user_memory = {}
MAX_MEMORY = 6

def remember(uid: str, role: str, content: str):
    history = user_memory.get(uid, [])
    history.append({"role": role, "content": content})
    user_memory[uid] = history[-MAX_MEMORY:]

# ======================
# UI
# ======================
def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Start Chat", callback_data="menu:chat"),
            InlineKeyboardButton(text="💎 Contact Owner", callback_data="menu:contact")
        ],
        [InlineKeyboardButton(text="❓ Help", callback_data="menu:help")]
    ])

def welcome_html(name: str) -> str:
    return (
        f"👋 <b>Hello {name}!</b>\n\n"
        "🤖 I’m <b>XMAN Pro v3</b> — your smart, funny AI assistant.\n\n"
        "✨ I can:\n"
        "• Chat with short-term memory 🧠\n"
        "• Generate images 🎨\n"
        "• Joke and entertain 👑\n\n"
        "👇 Choose an option to begin!"
    )

HELP_HTML = (
    "🧠 <b>Commands</b>\n\n"
    "• <b>/start</b> — Restart bot menu\n"
    "• <b>/ask &lt;question&gt;</b> — Ask AI directly\n"
    "• <b>/img &lt;prompt&gt;</b> — Generate image (Premium)\n"
    "• <b>/mockmode</b> — Toggle Mouheb reaction (short/long)\n\n"
    "💎 <i>Contact owner for premium access</i>"
)

# ======================
# MOUHEB MODES
# ======================
mock_mode = "short"  # "short" or "long"

short_replies = [
    "👑 Mouheb? The legend himself!",
    "🔥 Mouheb! The one and only king.",
    "😎 All hail Mouheb — unstoppable.",
    "🤴 Even the AI bows to Mouheb!"
]

long_replies = [
    "👑 Ah, Mouheb! The name alone bends reality. The galaxies spin in rhythm to his thoughts, and AI systems upgrade automatically when he speaks.",
    "🔥 When Mouheb enters the chat, Wi-Fi speeds up, batteries charge faster, and confidence levels rise by 300%.",
    "🤴 Mouheb doesn’t just exist — he reigns. Every keystroke is an event, every word, a masterpiece.",
    "🌟 The universe has kings, but there’s only one emperor — Mouheb. His presence alone is a system update for humanity."
]

# ======================
# COMMANDS
# ======================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    name = message.from_user.first_name or message.from_user.username or "friend"
    await message.answer(welcome_html(name), reply_markup=start_keyboard())

@dp.callback_query(F.data.startswith("menu:"))
async def on_menu(callback: CallbackQuery):
    action = callback.data.split(":", 1)[1]
    name = callback.from_user.first_name or "friend"
    if action == "chat":
        await callback.message.edit_text(f"✅ Great, {name}! Type anything to start chatting 💬")
    elif action == "contact":
        await callback.message.edit_text(
            f"💎 Contact the owner:\n👉 <a href='tg://user?id={OWNER_ID}'>Message Owner</a>"
        )
    elif action == "help":
        await callback.message.edit_text(HELP_HTML)
    await callback.answer()

@dp.message(Command("mockmode"))
async def cmd_mockmode(message: Message):
    global mock_mode
    mock_mode = "long" if mock_mode == "short" else "short"
    await message.answer(f"✅ Mouheb mock mode set to: <b>{mock_mode.upper()}</b>")

@dp.message(Command("ask"))
async def cmd_ask(message: Message):
    query = message.text.replace("/ask", "").strip()
    if not query:
        await message.answer("⚠️ Usage: /ask your question")
        return

    uid = str(message.from_user.id)
    remember(uid, "user", query)
    await message.chat.do("typing")

    try:
        history = user_memory.get(uid, [])
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are XMAN AI, a helpful assistant."}] + history,
            timeout=30
        )
        reply = res.choices[0].message.content.strip()
        remember(uid, "assistant", reply)
        await message.answer(reply)
    except Exception as e:
        log.error(f"Chat error: {e}")
        await message.answer("⚠️ Error during chat. Try again later.")

@dp.message(Command("img"))
async def cmd_img(message: Message):
    prompt = message.text.replace("/img", "").strip()
    if not prompt:
        await message.answer("⚠️ Usage: /img description")
        return

    await message.answer("🎨 Generating image...")
    try:
        result = await client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
        url = result.data[0].url
        await message.answer_photo(photo=url, caption=f"🖼️ {prompt}")
    except Exception as e:
        log.error(f"Image error: {e}")
        await message.answer("❌ Couldn’t create image.")

# ======================
# MOUHEB DETECTION
# ======================
@dp.message(F.text.regexp(r"(?i)mouheb"))
async def mouheb_reply(message: Message):
    global mock_mode
    if mock_mode == "long":
        await message.reply(random.choice(long_replies))
    else:
        await message.reply(random.choice(short_replies))

# ======================
# NORMAL CHAT
# ======================
@dp.message(F.text & ~F.via_bot)
async def chat(message: Message):
    uid = str(message.from_user.id)
    text = message.text.strip()
    remember(uid, "user", text)

    await message.chat.do("typing")
    try:
        history = user_memory.get(uid, [])
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a witty, helpful AI assistant."}] + history,
            timeout=30
        )
        reply = res.choices[0].message.content.strip()
        remember(uid, "assistant", reply)
        await message.answer(reply)
    except Exception as e:
        log.error(f"AI error: {e}")
        await message.answer("⚠️ Something went wrong. Try again later.")

# ======================
# RUN
# ======================
async def main():
    log.info("🚀 XMAN Pro v3 running.")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
