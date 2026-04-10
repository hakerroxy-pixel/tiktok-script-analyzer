import os
import socket
from dotenv import load_dotenv

load_dotenv()


def _find_writable_dir(candidates):
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except Exception:
            continue
    return candidates[-1]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    _DB_DIR = _find_writable_dir([
        "/data",
        "/opt/render/project/src/instance",
        os.path.join(os.path.dirname(__file__), "instance"),
    ])
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_DB_DIR, 'tiktok_analyzer.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    TMP_DIR = _find_writable_dir(["/data/tmp", "/tmp", os.path.join(os.path.dirname(__file__), "tmp")])

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
