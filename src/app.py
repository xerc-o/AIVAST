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


def create_app():
    app = Flask(__name__, template_folder=BASE_DIR / 'templates')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'AIVAST.db'}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(history_bp)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)