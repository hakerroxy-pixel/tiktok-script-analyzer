import os
from app import create_app
from routes.telegram import start_telegram_bot

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5080))

    try:
        start_telegram_bot(app)
    except Exception as e:
        print(f"Telegram bot not started: {e}")

    print(f"TikTok Script Analyzer running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
