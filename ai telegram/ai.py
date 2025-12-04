import json
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import os

# 🔐 Replace with your real credentials
TELEGRAM_TOKEN = "7908952043:AAFCen0ZLLSq1U2v-oKw-emiReRnkP9FaKw"
OPENAI_API_KEY = "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"
OWNER_ID = 7118377616  # 👈 Your Telegram ID here

client = OpenAI(api_key=OPENAI_API_KEY)

# 📁 Persistent user data
DATA_FILE = "user_roles.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_roles = json.load(f)
else:
    user_roles = {}

# 🏷️ Redeemable codes
redeem_codes = {
    "PREMIUM123": "premium"
}


def save_roles():
    with open(DATA_FILE, "w") as f:
        json.dump(user_roles, f)


# 🧩 Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    role = user_roles.get(user_id, "basic")
    await update.message.reply_text(
        f"Hello! I'm your AI bot 🤖\n"
        f"Your current plan: {role.upper()}\n"
        f"Use /redeem <code> to upgrade to Premium!"
    )


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    args = context.args

    if not args:
        await update.message.reply_text("⚠️ Usage: `/redeem <code>`")
        return

    code = args[0].strip()

    if code in redeem_codes:
        user_roles[user_id] = redeem_codes[code]
        save_roles()
        del redeem_codes[code]
        await update.message.reply_text("✅ Code accepted! You're now a PREMIUM user!")
    else:
        await update.message.reply_text("❌ Invalid or expired code.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    role = user_roles.get(user_id, "basic")
    user_input = update.message.text

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    thinking_msg = await update.message.reply_text("🤖 Thinking...")

    if role == "basic":
        system_message = "You are a simple assistant. Reply briefly and clearly."
    else:
        system_message = "You are a detailed, premium assistant. Reply with depth and creativity."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]
    )

    reply = response.choices[0].message.content.strip()
    await thinking_msg.edit_text(reply)


# 🖼️ Premium-only Image Generation
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    role = user_roles.get(user_id, "basic")

    if role != "premium":
        await update.message.reply_text("🚫 Only PREMIUM users can use /img.")
        return

    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Usage: `/img <description>`")
        return

    await update.message.reply_text("🎨 Generating your image, please wait...")

    # 🧠 Generate Image
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    image = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")

    image_url = image.data[0].url
    await update.message.reply_photo(image_url, caption=f"🖼️ Here’s your image!\nPrompt: {prompt}")


# 👑 Owner-only Command
async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can use this command.")
        return

    await update.message.reply_text(
        f"👑 Owner Panel\n\n"
        f"/list_users - View all users and roles\n"
        f"/add_code <CODE> - Create new premium code"
    )


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_ID:
        return

    msg = "📜 User Roles:\n\n"
    for uid, role in user_roles.items():
        msg += f"👤 {uid} → {role}\n"
    await update.message.reply_text(msg or "No users yet.")


async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_ID:
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usage: `/add_code <CODE>`")
        return

    code = args[0]
    redeem_codes[code] = "premium"
    await update.message.reply_text(f"✅ Added new premium code: {code}")


# 🚀 Bot Setup
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("redeem", redeem))
app.add_handler(CommandHandler("img", generate_image))
app.add_handler(CommandHandler("manage", manage))
app.add_handler(CommandHandler("list_users", list_users))
app.add_handler(CommandHandler("add_code", add_code))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

app.run_polling()
