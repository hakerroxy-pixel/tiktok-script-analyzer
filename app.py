import os
from flask import Flask
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(Config.TMP_DIR, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from routes.web import web_bp
    from routes.api import api_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
