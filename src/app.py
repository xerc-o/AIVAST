from flask import Flask
from dotenv import load_dotenv
import os
from pathlib import Path

from routes.main import main_bp
from routes.scan import scan_bp

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-key")

    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
