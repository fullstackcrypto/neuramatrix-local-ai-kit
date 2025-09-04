"""
API routes for NeuraMatrix Local AI Kit
Handles JSON API endpoints
"""
import os
import time
import uuid
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from app.models import db, Profile, Conversation, FileUpload
from app.services.security_service import SecurityService, SecurityError
from app.services.ai_service import AIService, AIServiceError, ModelNotAvailableError
from app.services.file_service import FileService
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get profile
        profile_id = session.get('profile_id')
        if not profile_id:
            return jsonify({'error': 'No profile selected'}), 401
        
        profile = Profile.query.get(profile_id)
        if not profile or not profile.is_active:
            return jsonify({'error': 'Invalid profile'}), 401
        
        # Security validation
        sanitized_message = SecurityService.sanitize_input(message)
        if SecurityService.check_sql_injection(sanitized_message):
            SecurityService.log_security_event(
                'sql_injection_attempt',
                {'message': message[:100], 'profile_id': profile_id},
                'critical'
            )
            return jsonify({'error': 'Invalid input detected'}), 400
        
        # Get AI service
        ai_service = AIService(current_app.config)
        
        # Generate session ID
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Get model preference
        model = data.get('model') or profile.preferences.get('preferred_model', current_app.config['DEFAULT_MODEL'])
        
        try:
            # Generate AI response with context
            context = profile.memory_context or ''
            start_time = time.time()
            
            ai_result = ai_service.generate_with_context(
                sanitized_message, 
                context, 
                model=model,
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 500)
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Save conversation
            conversation = Conversation(
                profile_id=profile.id,
                session_id=session_id,
                user_message=sanitized_message,
                ai_response=ai_result['response'],
                model_used=model,
                response_time=response_time,
                metadata={
                    'temperature': data.get('temperature', 0.7),
                    'cached': ai_result.get('cached', False),
                    'total_duration': ai_result.get('total_duration', 0)
                }
            )
            
            db.session.add(conversation)
            
            # Update profile memory if enabled
            if profile.preferences.get('enable_memory', True):
                profile.add_memory(f"User: {sanitized_message}\nAssistant: {ai_result['response']}")
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'response': ai_result['response'],
                'session_id': session_id,
                'model': model,
                'response_time': response_time,
                'conversation_id': conversation.id,
                'cached': ai_result.get('cached', False)
            })
            
        except ModelNotAvailableError as e:
            logger.error(f"Model not available: {e}")
            return jsonify({'error': f'AI model not available: {str(e)}'}), 503
        
        except AIServiceError as e:
            logger.error(f"AI service error: {e}")
            return jsonify({'error': 'AI service temporarily unavailable'}), 503
        
    except SecurityError as e:
        logger.warning(f"Security error in chat: {e}")
        return jsonify({'error': 'Security validation failed'}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get profile
        profile_id = session.get('profile_id')
        if not profile_id:
            return jsonify({'error': 'No profile selected'}), 401
        
        profile = Profile.query.get(profile_id)
        if not profile or not profile.is_active:
            return jsonify({'error': 'Invalid profile'}), 401
        
        # Validate filename
        is_valid, result = SecurityService.validate_filename(file.filename)
        if not is_valid:
            return jsonify({'error': result}), 400
        
        secured_filename = result
        
        # Check file extension
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        extension = secured_filename.rsplit('.', 1)[1].lower()
        if extension not in allowed_extensions:
            return jsonify({'error': f'File type not allowed: {extension}'}), 400
        
        # Use file service
        file_service = FileService(current_app.config)
        
        try:
            # Process file upload
            upload_result = file_service.process_upload(file, profile.id)
            
            # Generate summary using AI
            ai_service = AIService(current_app.config)
            
            if upload_result['content']:
                try:
                    summary = ai_service.summarize_text(upload_result['content'])
                    upload_result['summary']