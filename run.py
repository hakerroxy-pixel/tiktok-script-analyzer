import os
from app import create_app
from routes.telegram import start_telegram_bot

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5080))

    start_telegram_bot(app)

    print(f"TikTok Script Analyzer running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
