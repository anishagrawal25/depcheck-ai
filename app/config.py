import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "5"))


def get_config():
    return {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "REQUEST_TIMEOUT": int(os.getenv("REQUEST_TIMEOUT", "5")),
    }
