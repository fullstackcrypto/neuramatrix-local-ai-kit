"""
Configuration settings for NeuraMatrix Local AI Kit
"""
import os
from pathlib import Path
from typing import List
import secrets

# Base directory
BASE_DIR = Path(__file__).parent.parent.absolute()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = False
    TESTING = False
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/neuramatrix.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # AI Model settings
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'localhost')
    OLLAMA_PORT = int(os.environ.get('OLLAMA_PORT', '11434'))
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'mistral')
    AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '30'))  # seconds
    
    # File upload settings
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'json'}
    
    # Security settings
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'neuramatrix.log'
    
    # Plugin settings
    PLUGIN_FOLDER = BASE_DIR / 'plugins'
    PLUGIN_TIMEOUT = 10  # seconds
    ALLOWED_PLUGIN_IMPORTS = {'json', 'datetime', 'requests', 'time', 'math', 're'}
    
    # Backup settings
    BACKUP_FOLDER = BASE_DIR / 'backups'
    MAX_BACKUPS = 10
    AUTO_BACKUP_INTERVAL = 24  # hours
    
    # Performance
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        Config.UPLOAD_FOLDER.mkdir(exist_ok=True)
        Config.BACKUP_FOLDER.mkdir(exist_ok=True)
        Config.PLUGIN_FOLDER.mkdir(exist_ok=True)
        (BASE_DIR / 'logs').mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable for development ease
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Stricter rate limits
    RATELIMIT_DEFAULT = "50 per hour"
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Set up file logging
            file_handler = RotatingFileHandler(
                str(cls.LOG_FILE), 
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('NeuraMatrix startup')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = BASE_DIR / 'test_uploads'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    return config[os.environ.get('FLASK_ENV', 'default')]