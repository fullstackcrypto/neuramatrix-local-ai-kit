"""
Database models for NeuraMatrix Local AI Kit
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()

class Profile(db.Model):
    """User profile model"""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    preferences = db.Column(JSON, default=dict)
    memory_context = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<Profile {self.username}>'
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'preferences': self.preferences or {},
            'memory_context': self.memory_context,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class Conversation(db.Model):
    """Conversation history model"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False, index=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    model_used = db.Column(db.String(50), nullable=False)
    response_time = db.Column(db.Integer)  # milliseconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    extra_data = db.Column(JSON, default=dict)  # Changed from 'metadata' to 'extra_data'
    
    def __repr__(self):
        return f'<Conversation {self.id} for Profile {self.profile_id}>'
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'model_used': self.model_used,
            'response_time': self.response_time,
            'timestamp': self.timestamp.isoformat(),
            'extra_data': self.extra_data or {}
        }

class FileUpload(db.Model):
    """File upload tracking model"""
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed = db.Column(db.Boolean, default=False, nullable=False)
    summary = db.Column(db.Text)
    file_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA-256 hash
    
    def __repr__(self):
        return f'<FileUpload {self.original_filename} by Profile {self.profile_id}>'
    
    def to_dict(self):
        """Convert file upload to dictionary"""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'processed': self.processed,
            'summary': self.summary,
            'file_hash': self.file_hash
        }
