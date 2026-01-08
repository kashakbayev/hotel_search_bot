import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Put it in .env")
if not RAPIDAPI_KEY:
    raise RuntimeError("RAPIDAPI_KEY is missing. Put it in .env")
