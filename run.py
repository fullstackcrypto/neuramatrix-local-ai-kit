#!/usr/bin/env python3
"""
NeuraMatrix Local AI Kit - Main Application Runner
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import logging

def main():
    """Main application entry point"""
    
    # Set up environment
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import and create Flask application
        from app import create_app
        app = create_app()
        
        logger.info("Application created successfully")
        
        # Get configuration
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        logger.info(f"Starting NeuraMatrix on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        logger.error(f"Error details: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
