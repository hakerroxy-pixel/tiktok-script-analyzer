import os
import socket
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Use /data for Railway persistent volume, fallback to local instance/ dir
    _DB_DIR = "/data" if os.path.isdir("/data") else os.path.join(os.path.dirname(__file__), "instance")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_DB_DIR, 'tiktok_analyzer.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TMP_DIR = "/data/tmp" if os.path.isdir("/data") else os.path.join(os.path.dirname(__file__), "tmp")

    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
