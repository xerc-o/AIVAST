from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def _safe_json_loads(data_string):
    """Safely loads a JSON string, returns empty dict or string on failure."""
    if data_string is None:
        return None
    try:
        return json.loads(data_string)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data", "raw_data": data_string}

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ScanHistory(db.Model):
    """Model untuk menyimpan history scanning."""
    
    __tablename__ = "scan_history"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Add user_id foreign key
    target = db.Column(db.String(500), nullable=False, index=True)
    tool = db.Column(db.String(50), nullable=False)
    command = db.Column(db.Text, nullable=False)
    
    # Fields for async task tracking
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    pid = db.Column(db.Integer, nullable=True)
    stdout_path = db.Column(db.String(500), nullable=True)
    stderr_path = db.Column(db.String(500), nullable=True)

    # Fields for results
    execution_result = db.Column(db.Text)  # JSON string
    analysis_result = db.Column(db.Text)   # JSON string
    risk_level = db.Column(db.String(20), index=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    start_time = db.Column(db.DateTime, nullable=True) # New column
    
    def to_dict(self):
        """Convert model ke dictionary."""
        return {
            "id": self.id,
            "target": self.target,
            "tool": self.tool,
            "command": _safe_json_loads(self.command),
            "status": self.status,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "execution": _safe_json_loads(self.execution_result),
            "analysis": _safe_json_loads(self.analysis_result)
        }
    
    def __repr__(self):
        return f"<ScanHistory {self.id}: {self.target} ({self.tool})>"