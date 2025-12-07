# discord_bot.py
import discord
from discord.ext import commands
from nlp_parser import parse_user_text
from calculator import calculate_for_patch
from config import DISCORD_TOKEN

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command(name="primos")
async def primos(ctx, *, arg: str = None):
    if not arg:
        await ctx.send("Usage: `!primos 6.3 welkin new map` or `!primos f2p 6.3`")
        return
    parsed = parse_user_text(arg)
    version = parsed.get("version") or "6.2"
    player = parsed.get("player_type", "f2p")
    result = calculate_for_patch(version, player_type=player,
                                 include_story=parsed.get("include_story", True),
                                 include_character=parsed.get("include_character", True),
                                 include_map=parsed.get("include_map", False))
    lines = [f"Patch: {result['patch']} ({result['patch_date']})"]
    for k, v in result["details"].items():
        lines.append(f"{k}: {v}")
    lines.append(f"**TOTAL: {result['total']}**")
    await ctx.send("\n".join(lines))

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
