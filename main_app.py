"""
NeuraMatrix Local AI Kit Application Factory
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config.settings import config, get_config
from app.models import db
from app.services.security_service import SecurityService, RateLimitExceeded

# Initialize extensions
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.api_routes import api_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.system_routes import system_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(system_bp, url_prefix='/system')
    
    # Configure logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register request handlers
    register_request_handlers(app)
    
    return app


def setup_logging(app):
    """Setup application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'neuramatrix.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NeuraMatrix startup')


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def too_large(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'File too large'}), 413
        return jsonify({'error': 'File too large'}), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        SecurityService.log_security_event(
            'rate_limit_exceeded',
            {'path': request.path, 'method': request.method},
            'warning'
        )
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(error):
        return jsonify({'error': str(error)}), 429


def register_request_handlers(app):
    """Register request handlers"""
    
    @app.before_request
    def before_request():
        # Security checks
        client_id = SecurityService.get_client_identifier()
        
        # Rate limiting for API endpoints
        if request.path.startswith('/api/'):
            if not SecurityService.rate_limit_check(client_id):
                raise RateLimitExceeded("Rate limit exceeded")
        
        # Log suspicious requests
        if request.method in ['POST', 'PUT', 'DELETE']:
            if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
                SecurityService.log_security_event(
                    'oversized_request',
                    {
                        'content_length': request.content_length,
                        'max_allowed': app.config['MAX_CONTENT_LENGTH'],
                        'path': request.path
                    },
                    'warning'
                )
    
    @app.after_request
    def after_request(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS for production
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    @app.context_processor
    def inject_template_vars():
        """Inject common template variables"""
        return {
            'app_name': 'NeuraMatrix',
            'app_version': '2.0.0'
        }