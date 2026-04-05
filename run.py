from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    local_ip = Config.get_local_ip()
    print(f"TikTok Script Analyzer running at:")
    print(f"  Local:   http://127.0.0.1:5060")
    print(f"  Network: http://{local_ip}:5060")
    app.run(host="0.0.0.0", port=5060, debug=True)
