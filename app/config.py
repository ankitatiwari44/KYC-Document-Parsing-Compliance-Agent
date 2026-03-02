import os
from dotenv import load_dotenv
from google import genai
from pathlib import Path


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "models/gemini-flash-latest"