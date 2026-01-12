from flask import Flask
from dotenv import load_dotenv
import os
from pathlib import Path
from routes.main import main_bp
from routes.scan import scan_bp
from models import db, User, ScanHistory
from routes.history import history_bp
from routes.auth import auth_bp
from flask_login import LoginManager
from flask.cli import with_appcontext
import click
import logging # Import logging module

# Configure logging at the beginning
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def create_app(config_overrides=None):
    app = Flask(__name__,
                template_folder=BASE_DIR / 'templates',
                static_folder=BASE_DIR / 'static',
                instance_path=BASE_DIR / 'instance')
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configuration from environment variables
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(app.instance_path, 'AIVAST.db')}?timeout={os.getenv('DATABASE_TIMEOUT', 15)}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Apply overrides for testing
    if config_overrides:
        app.config.update(config_overrides)
    
    # Initialize database
    db.init_app(app)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.index' # Arahkan ke halaman login jika belum login

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints with API versioning
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(scan_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")

    # Custom CLI commands
    @app.cli.command("create-db")
    def create_db_command():
        """Creates the database tables and a default user."""
        db.create_all()
        # Add default user if not exists
        if not User.query.filter_by(email="test@example.com").first():
            password = click.prompt("Enter password for default user", hide_input=True, confirmation_prompt=True)
            default_user = User(username="testuser", email="test@example.com")
            default_user.set_password(password)
            db.session.add(default_user)
            db.session.commit()
            click.echo("Default user 'test@example.com' added.")
        click.echo("Database tables created.")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)