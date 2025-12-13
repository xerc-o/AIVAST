from flask import Flask
from dotenv import load_dotenv
import os

from routes.main import main_bp
from routes.scan import scan_bp

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-key")

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
