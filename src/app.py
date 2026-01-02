from flask import Flask
from dotenv import load_dotenv
import os
from pathlib import Path
from routes.main import main_bp
from routes.scan import scan_bp
from models import db
from routes.history import history_bp

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def create_app(config_overrides=None):
    app = Flask(__name__, template_folder=BASE_DIR / 'templates')
    
    # Configuration from environment variables
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'AIVAST.db'}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Apply overrides for testing
    if config_overrides:
        app.config.update(config_overrides)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints with API versioning
    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)