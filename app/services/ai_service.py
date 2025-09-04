"""
AI Service for NeuraMatrix Local AI Kit
Handles communication with Ollama and AI model management
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import ollama
from functools import wraps
import json
import hashlib

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI Service errors"""
    pass


class ModelNotAvailableError(AIServiceError):
    """Raised when requested AI model is not available"""
    pass


class AIService:
    """Service class for AI operations"""
    
    def __init__(self, config):
        self.host = config.OLLAMA_HOST
        self.port = config.OLLAMA_PORT
        self.default_model = config.DEFAULT_MODEL
        self.timeout = config.AI_TIMEOUT
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Initialize thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Response cache with TTL
        self.cache = {}
        self.cache_ttl = {}
        
        # Initialize Ollama client
        try:
            self.client = ollama.Client(host=self.base_url)
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.client = None
    
    def _cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key for response caching"""
        key_data = f"{prompt}:{model}:{json.dumps(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str, ttl_seconds: int = 300) -> Optional[str]:
        """Get cached response if still valid"""
        if cache_key in self.cache:
            cached_time = self.cache_ttl.get(cache_key, 0)
            if time.time() - cached_time < ttl_seconds:
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.cache[cache_key]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                del self.cache_ttl[cache_key]
        return None
    
    def _set_cached_response(self, cache_key: str, response: str):
        """Set cached response"""
        self.cache[cache_key] = response
        self.cache_ttl[cache_key] = time.time()
        logger.debug(f"Cached response for key: {cache_key}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'service': 'ollama',
                    'version': response.json().get('version', 'unknown'),
                    'host': self.host,
                    'port': self.port
                }
        except (RequestException, ConnectionError, Timeout) as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                'status': 'unhealthy',
                'service': 'ollama',
                'error': str(e),
                'host': self.host,
                'port': self.port
            }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            if not self.client:
                raise AIServiceError("Ollama client not initialized")
            
            models = self.client.list()
            return [
                {
                    'name': model.get('name', ''),
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', ''),
                    'digest': model.get('digest', '')
                }
                for model in models.get('models', [])
            ]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise AIServiceError(f"Failed to list models: {e}")
    
    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available"""
        try:
            available_models = self.list_available_models()
            return any(model['name'] == model_name for model in available_models)
        except AIServiceError:
            return False
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize user input prompt"""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        
        # Remove excessive whitespace and limit length
        prompt = prompt.strip()
        if len(prompt) > 8000:  # Reasonable limit
            logger.warning("Prompt truncated due to length")
            prompt = prompt[:8000]
        
        return prompt
    
    def _generate_sync(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """Synchronous generation method"""
        if not self.client:
            raise AIServiceError("Ollama client not available")
        
        model = model or self.default_model
        
        # Validate model availability
        if not self.validate_model(model):
            raise ModelNotAvailableError(f"Model '{model}' is not available")
        
        # Sanitize input
        prompt = self._sanitize_prompt(prompt)
        
        # Check cache first
        cache_key = self._cache_key(prompt, model, **kwargs)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return {
                'response': cached_response,
                'model': model,
                'created_at': time.time(),
                'cached': True
            }
        
        try:
            start_time = time.time()
            
            # Generate response
            response = self.client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                options=kwargs
            )
            
            end_time = time.time()
            response_time = int((end_time - start_time) * 1000)  # milliseconds
            
            ai_response = response.get('response', '')
            
            # Cache the response
            self._set_cached_response(cache_key, ai_response)
            
            return {
                'response': ai_response,
                'model': model,
                'created_at': end_time,
                'response_time': response_time,
                'cached': False,
                'total_duration': response.get('total_duration', 0),
                'load_duration': response.get('load_duration', 0),
                'prompt_eval_count': response.get('prompt_eval_count', 0),
                'eval_count': response.get('eval_count', 0)
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise AIServiceError(f"Failed to generate response: {e}")
    
    async def generate_async(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """Asynchronous generation method"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    self._generate_sync, 
                    prompt, 
                    model, 
                    **kwargs
                ),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise AIServiceError(f"AI generation timed out after {self.timeout} seconds")
        except Exception as e:
            raise AIServiceError(f"Async generation failed: {e}")
    
    def generate_response(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate AI response (synchronous wrapper)"""
        try:
            result = self._generate_sync(prompt, model, **kwargs)
            return result['response']
        except Exception as e:
            logger.error(f"Generate response failed: {e}")
            raise
    
    def generate_with_context(self, prompt: str, context: str = "", model: str = None, **kwargs) -> Dict[str, Any]:
        """Generate response with conversation context"""
        if context:
            full_prompt = f"Context: {context}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = prompt
            
        return self._generate_sync(full_prompt, model, **kwargs)
    
    def summarize_text(self, text: str, max_length: int = 200, model: str = None) -> str:
        """Summarize given text"""
        if len(text) < 100:  # Don't summarize very short texts
            return text
            
        summary_prompt = f"""Please provide a concise summary of the following text in no more than {max_length} characters:

{text}

Summary:"""
        
        try:
            result = self._generate_sync(
                summary_prompt, 
                model,
                temperature=0.3,  # Lower temperature for more focused summaries
                max_tokens=100
            )
            return result['response']
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return f"Error: Could not summarize text - {str(e)}"
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        self.cache_ttl.clear()
        logger.info("AI response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'total_cached_responses': len(self.cache)
        }
    
    def __del__(self):
        """Cleanup method"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)