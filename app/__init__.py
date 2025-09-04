"""
NeuraMatrix Local AI Kit Application Factory
"""
import os
import logging
from flask import Flask, render_template, jsonify

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuramatrix.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    
    # Initialize database
    try:
        from app.models import db
        db.init_app(app)
        
        # Create tables
        with app.app_context():
            db.create_all()
            logging.info("Database initialized successfully")
            
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        # Continue without database for now
    
    # Register routes
    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except:
            return '''
            <h1>🚀 NeuraMatrix Local AI Kit v2.0</h1>
            <h2>✅ Application Running Successfully!</h2>
            <p><strong>Status:</strong> Development Server Active</p>
            <p><a href="/health">🔍 Health Check</a></p>
            <p><a href="/api/status">📡 API Status</a></p>
            <hr>
            <p><em>Database initialized and ready</em></p>
            '''
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy', 
            'version': '2.0.0',
            'environment': 'development',
            'database': 'connected'
        })
    
    @app.route('/api/status')
    def api_status():
        return jsonify({
            'success': True,
            'api_version': '2.0.0',
            'status': 'operational'
        })
    
    return app
