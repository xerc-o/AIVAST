from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class ScanHistory(db.Model):
    """Model untuk menyimpan history scanning."""
    
    __tablename__ = "scan_history"
    
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String(500), nullable=False, index=True)
    tool = db.Column(db.String(50), nullable=False)
    command = db.Column(db.Text, nullable=False)
    execution_result = db.Column(db.Text)  # JSON string
    analysis_result = db.Column(db.Text)   # JSON string
    risk_level = db.Column(db.String(20), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert model ke dictionary."""
        return {
            "id": self.id,
            "target": self.target,
            "tool": self.tool,
            "command": self.command,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "execution": json.loads(self.execution_result) if self.execution_result else None,
            "analysis": json.loads(self.analysis_result) if self.analysis_result else None
        }
    
    def __repr__(self):
        return f"<ScanHistory {self.id}: {self.target} ({self.tool})>"