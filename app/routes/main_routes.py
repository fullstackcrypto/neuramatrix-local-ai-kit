"""
Main routes for NeuraMatrix Local AI Kit
Handles the primary web interface
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models import db, Profile, Conversation
from app.services.security_service import SecurityService
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main dashboard page"""
    # Get current profile from session
    profile_id = session.get('profile_id')
    current_profile = None
    
    if profile_id:
        current_profile = Profile.query.get(profile_id)
    
    # Get recent conversations for dashboard
    recent_conversations = []
    if current_profile:
        recent_conversations = Conversation.query.filter_by(
            profile_id=current_profile.id
        ).order_by(Conversation.timestamp.desc()).limit(5).all()
    
    return render_template('index.html', 
                         current_profile=current_profile,
                         recent_conversations=recent_conversations)


@main_bp.route('/chat')
def chat():
    """Chat interface page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        flash('Please select a profile first', 'warning')
        return redirect(url_for('main.select_profile'))
    
    current_profile = Profile.query.get(profile_id)
    if not current_profile:
        flash('Profile not found', 'error')
        return redirect(url_for('main.select_profile'))
    
    # Get conversation history
    conversations = Conversation.query.filter_by(
        profile_id=current_profile.id
    ).order_by(Conversation.timestamp.asc()).limit(50).all()
    
    return render_template('chat.html', 
                         current_profile=current_profile,
                         conversations=conversations)


@main_bp.route('/select_profile')
def select_profile():
    """Profile selection page"""
    profiles = Profile.query.filter_by(is_active=True).all()
    return render_template('select_profile.html', profiles=profiles)


@main_bp.route('/set_profile/<int:profile_id>')
def set_profile(profile_id):
    """Set current profile in session"""
    profile = Profile.query.get_or_404(profile_id)
    
    if not profile.is_active:
        flash('Profile is not active', 'error')
        return redirect(url_for('main.select_profile'))
    
    session['profile_id'] = profile.id
    flash(f'Profile set to {profile.display_name}', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/upload')
def upload():
    """File upload page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        flash('Please select a profile first', 'warning')
        return redirect(url_for('main.select_profile'))
    
    current_profile = Profile.query.get(profile_id)
    if not current_profile:
        flash('Profile not found', 'error')
        return redirect(url_for('main.select_profile'))
    
    return render_template('upload.html', current_profile=current_profile)


@main_bp.route('/plugins')
def plugins():
    """Plugin management page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        flash('Please select a profile first', 'warning')
        return redirect(url_for('main.select_profile'))
    
    current_profile = Profile.query.get(profile_id)
    if not current_profile:
        flash('Profile not found', 'error')
        return redirect(url_for('main.select_profile'))
    
    from app.services.plugin_service import PluginService
    plugin_service = PluginService(current_app.config)
    
    try:
        available_plugins = plugin_service.list_available_plugins()
        plugin_states = plugin_service.get_all_plugin_states()
    except Exception as e:
        logger.error(f"Failed to load plugins: {e}")
        flash('Failed to load plugins', 'error')
        available_plugins = []
        plugin_states = {}
    
    return render_template('plugins.html', 
                         current_profile=current_profile,
                         available_plugins=available_plugins,
                         plugin_states=plugin_states)


@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check AI service
        ai_service = AIService(current_app.config)
        ai_health = ai_service.health_check()
        
        health_status = {
            'status': 'healthy',
            'database': 'connected',
            'ai_service': ai_health,
            'version': '2.0.0'
        }
        
        return health_status, 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status = {
            'status': 'unhealthy',
            'error': str(e),
            'version': '2.0.0'
        }
        return health_status, 500


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/settings')
def settings():
    """Settings page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        flash('Please select a profile first', 'warning')
        return redirect(url_for('main.select_profile'))
    
    current_profile = Profile.query.get(profile_id)
    if not current_profile:
        flash('Profile not found', 'error')
        return redirect(url_for('main.select_profile'))
    
    return render_template('settings.html', current_profile=current_profile)