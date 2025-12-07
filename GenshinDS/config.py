# config.py
import os

# Prefer environment variables for security:
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "MTQ0NzI2ODE1MjM0OTE2MzU1MA.Gj06hN.8711E1A02wm97NOmT_nUoqDfbGXksgt-wFRsCI")

# Default model to call (you can change)
OPENAI_MODEL = "gpt-4o"        # or "gpt-4o-mini", "gpt-4o-realtime-preview" etc.
