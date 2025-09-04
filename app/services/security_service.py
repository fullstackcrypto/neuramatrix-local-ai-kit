"""
Security Service for NeuraMatrix Local AI Kit
Handles input validation, sanitization, and security checks
"""
import re
import hashlib
import secrets
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import bleach
from werkzeug.utils import secure_filename
import validators
from flask import request, current_app
import time
import json

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class RateLimitExceeded(SecurityError):
    """Raised when rate limit is exceeded"""
    pass


class SecurityService:
    """Service class for security operations"""
    
    # Rate limiting storage (in production, use Redis or database)
    _rate_limit_storage = {}
    
    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    # Dangerous file patterns
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar', 'py', 'php',
        'pl', 'sh', 'ps1', 'msi', 'app', 'deb', 'rpm', 'dmg', 'iso', 'bin'
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|;|\/\*|\*\/)",
        r"(\b(xp_|sp_)\w+)",
        r"(char\s*\(\d+\))",
    ]
    
    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 5000) -> str:
        """Sanitize user input to prevent XSS and other attacks"""
        if not user_input or not isinstance(user_input, str):
            return ""
        
        # Limit input length
        if len(user_input) > max_length:
            logger.warning(f"Input truncated from {len(user_input)} to {max_length} characters")
            user_input = user_input[:max_length]
        
        # Remove null bytes and control characters
        user_input = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', user_input)
        
        # Sanitize HTML
        sanitized = bleach.clean(
            user_input,
            tags=SecurityService.ALLOWED_TAGS,
            attributes=SecurityService.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return sanitized.strip()
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """Validate uploaded filename for security"""
        if not filename:
            return False, "Filename cannot be empty"
        
        # Secure the filename
        secured_name = secure_filename(filename)
        if not secured_name:
            return False, "Invalid filename after sanitization"
        
        # Check file extension
        if '.' not in secured_name:
            return False, "File must have an extension"
        
        extension = secured_name.rsplit('.', 1)[1].lower()
        
        # Check for dangerous extensions
        if extension in SecurityService.DANGEROUS_EXTENSIONS:
            return False, f"File type '{extension}' not allowed for security reasons"
        
        # Check filename length
        if len(secured_name) > 255:
            return False, "Filename too long"
        
        # Check for path traversal attempts
        if '..' in secured_name or '/' in secured_name or '\\' in secured_name:
            return False, "Invalid characters in filename"
        
        return True, secured_name
    
    @staticmethod
    def validate_file_content(file_path: Path, allowed_extensions: set) -> Tuple[bool, str]:
        """Validate file content and extension"""
        try:
            extension = file_path.suffix.lower().lstrip('.')
            
            if extension not in allowed_extensions:
                return False, f"File extension '{extension}' not allowed"
            
            # Check file size (additional safety)
            file_size = file_path.stat().st_size
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            
            if file_size > max_size:
                return False, f"File too large: {file_size} bytes (max: {max_size})"
            
            # Basic content validation for text files
            if extension in {'txt', 'md'}:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024)  # Read first 1KB
                        # Check for binary content in text files
                        if '\0' in content:
                            return False, "Binary content detected in text file"
                except UnicodeDecodeError:
                    return False, "Invalid text encoding"
            
            return True, "File validation passed"
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False, f"File validation failed: {str(e)}"
    
    @staticmethod
    def check_sql_injection(input_string: str) -> bool:
        """Check for SQL injection patterns"""
        if not input_string:
            return False
        
        input_upper = input_string.upper()
        
        for pattern in SecurityService.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL for security"""
        if not url:
            return False, "URL cannot be empty"
        
        # Basic URL validation
        if not validators.url(url):
            return False, "Invalid URL format"
        
        # Check for dangerous protocols
        dangerous_protocols = {'javascript:', 'data:', 'vbscript:', 'file:'}
        url_lower = url.lower()
        
        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                return False, f"Protocol '{protocol}' not allowed"
        
        # Only allow HTTP and HTTPS
        if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
            return False, "Only HTTP and HTTPS protocols allowed"
        
        return True, "URL validation passed"
    
    @staticmethod
    def rate_limit_check(identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """Check rate limiting (per hour by default)"""
        current_time = time.time()
        window_start = current_time - window
        
        # Clean old entries
        SecurityService._rate_limit_storage = {
            k: [timestamp for timestamp in v if timestamp > window_start]
            for k, v in SecurityService._rate_limit_storage.items()
            if any(timestamp > window_start for timestamp in v)
        }
        
        # Check current identifier
        if identifier not in SecurityService._rate_limit_storage:
            SecurityService._rate_limit_storage[identifier] = []
        
        request_times = SecurityService._rate_limit_storage[identifier]
        
        if len(request_times) >= limit:
            logger.warning(f"Rate limit exceeded for {identifier}: {len(request_times)} requests")
            return False
        
        # Add current request
        request_times.append(current_time)
        return True
    
    @staticmethod
    def get_client_identifier() -> str:
        """Get unique client identifier for rate limiting"""
        # In production, consider using more sophisticated methods
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Create hash of IP + User Agent for privacy
        identifier_string = f"{client_ip}:{user_agent}"
        return hashlib.sha256(identifier_string.encode()).hexdigest()[:16]
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        if not token or not session_token:
            return False
        return secrets.compare_digest(token, session_token)
    
    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Generate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            return ""
    
    @staticmethod
    def validate_json_input(json_input: str, max_depth: int = 5) -> Tuple[bool, Any]:
        """Validate JSON input for security"""
        if not json_input:
            return False, "JSON input cannot be empty"
        
        try:
            # Parse JSON with size limit
            if len(json_input) > 10000:  # 10KB limit
                return False, "JSON input too large"
            
            data = json.loads(json_input)
            
            # Check nesting depth to prevent JSON bombs
            def check_depth(obj, current_depth=0):
                if current_depth > max_depth:
                    raise ValueError("JSON nesting too deep")
                
                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, current_depth + 1)
                elif isinstance(obj, list):
                    for item in obj:
                        check_depth(item, current_depth + 1)
            
            check_depth(data)
            return True, data
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"JSON validation error: {e}")
            return False, "JSON validation failed"
    
    @staticmethod
    def sanitize_plugin_code(code: str) -> Tuple[bool, str]:
        """Validate and sanitize plugin code"""
        if not code:
            return False, "Plugin code cannot be empty"
        
        # Check for dangerous imports
        dangerous_imports = {
            'os', 'sys', 'subprocess', 'eval', 'exec', 'compile', 'open',
            '__import__', 'importlib', 'ast', 'types', 'builtins'
        }
        
        code_lines = code.split('\n')
        for line_num, line in enumerate(code_lines, 1):
            line_stripped = line.strip()
            
            # Check for dangerous function calls
            if any(dangerous in line_stripped for dangerous in dangerous_imports):
                return False, f"Dangerous import/function detected at line {line_num}"
            
            # Check for eval/exec usage
            if re.search(r'\b(eval|exec|compile)\s*\(', line_stripped):
                return False, f"Dangerous function call detected at line {line_num}"
        
        return True, "Plugin code validation passed"
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "warning"):
        """Log security events"""
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        log_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'client_ip': client_ip,
            'user_agent': user_agent,
            'details': details,
            'severity': severity
        }
        
        if severity == "critical":
            logger.critical(f"SECURITY EVENT: {json.dumps(log_entry)}")
        elif severity == "error":
            logger.error(f"SECURITY EVENT: {json.dumps(log_entry)}")
        else:
            logger.warning(f"SECURITY EVENT: {json.dumps(log_entry)}")
    
    @staticmethod
    def validate_profile_data(profile_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate profile data"""
        required_fields = ['username', 'display_name']
        
        for field in required_fields:
            if field not in profile_data:
                return False, f"Missing required field: {field}"
            
            if not isinstance(profile_data[field], str):
                return False, f"Field {field} must be a string"
            
            if not profile_data[field].strip():
                return False, f"Field {field} cannot be empty"
        
        # Validate username format
        username = profile_data['username']
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}, username):
            return False, "Username must be 3-30 characters, alphanumeric with _ or - only"
        
        # Validate display name
        display_name = profile_data['display_name']
        if len(display_name) > 100:
            return False, "Display name too long (max 100 characters)"
        
        # Validate preferences if present
        if 'preferences' in profile_data:
            if not isinstance(profile_data['preferences'], dict):
                return False, "Preferences must be a dictionary"
        
        return True, "Profile data validation passed"