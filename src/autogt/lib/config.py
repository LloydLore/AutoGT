"""Configuration management for AutoGT."""

import os
from typing import Optional, Dict, Any


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


class Config:
    """AutoGT configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment and files."""
        # Default configuration
        self._config = {
            'database': {
                'url': os.getenv('AUTOGT_DATABASE_URL', 'sqlite:///autogt.db')
            },
            'api': {
                'gemini_key': os.getenv('AUTOGT_GEMINI_API_KEY', '')
            },
            'logging': {
                'level': os.getenv('AUTOGT_LOG_LEVEL', 'INFO')
            }
        }
    
    def get_database_url(self) -> str:
        """Get database URL."""
        return self._config['database']['url']
    
    def get_gemini_config(self):
        """Get Gemini API configuration."""
        from collections import namedtuple
        
        # Create a config object with all required fields
        GeminiConfig = namedtuple('GeminiConfig', ['api_key', 'model_name', 'base_url'])
        
        # Try multiple environment variable names
        api_key = (
            self._config['api']['gemini_key'] or 
            os.getenv('GEMINI_API_KEY') or 
            os.getenv('GOOGLE_API_KEY')
        )
        
        if not api_key:
            # Return mock config for demo purposes
            return GeminiConfig(
                api_key='demo-key-not-configured',
                model_name='gemini-2.0-flash-exp',
                base_url='https://generativelanguage.googleapis.com/v1beta/openai'
            )
        
        return GeminiConfig(
            api_key=api_key,
            model_name=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
            base_url='https://generativelanguage.googleapis.com/v1beta/openai'
        )
    
    def get(self, key: str, default=None):
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
