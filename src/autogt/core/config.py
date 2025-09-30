"""Configuration management for AutoGT TARA Platform."""

import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class AutoGTConfig(BaseSettings):
    """Main configuration class for AutoGT platform."""
    
    # API Configuration
    gemini_api_key: Optional[str] = Field(
        default=None,
        env="AUTOGT_GEMINI_API_KEY",
        description="Google Gemini API key for AI integration"
    )
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        env="AUTOGT_GEMINI_BASE_URL",
        description="Gemini API base URL"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        env="AUTOGT_GEMINI_MODEL", 
        description="Gemini model to use for AI analysis"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./autogt.db",
        env="AUTOGT_DATABASE_URL",
        description="Database connection URL"
    )
    
    # Application Configuration
    app_name: str = Field(
        default="AutoGT TARA Platform",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        env="AUTOGT_DEBUG",
        description="Enable debug mode"
    )
    
    # Performance Configuration
    max_file_size_mb: int = Field(
        default=10,
        env="AUTOGT_MAX_FILE_SIZE_MB",
        description="Maximum file upload size in MB"
    )
    single_analysis_timeout_seconds: int = Field(
        default=10,
        description="Timeout for single asset analysis"
    )
    full_model_timeout_seconds: int = Field(
        default=300,  # 5 minutes
        description="Timeout for full vehicle model analysis"
    )
    batch_processing_target_per_minute: int = Field(
        default=100,
        description="Target batch processing throughput"
    )
    
    # Audit Trail Configuration
    audit_retention_years: int = Field(
        default=3,
        description="Audit trail retention period in years"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="AUTOGT_LOG_LEVEL",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format string"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_config_dir() -> Path:
    """Get configuration directory path."""
    config_dir = Path.home() / ".autogt"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def load_config_file(config_path: Optional[Path] = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = get_config_dir() / "config.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config_file(config_data: dict, config_path: Optional[Path] = None):
    """Save configuration to YAML file."""
    if config_path is None:
        config_path = get_config_dir() / "config.yaml"
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)


# Global configuration instance
_config: Optional[AutoGTConfig] = None


def get_config() -> AutoGTConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        # Load from file first, then override with environment variables
        file_config = load_config_file()
        _config = AutoGTConfig(**file_config)
    return _config


def set_config(config: AutoGTConfig):
    """Set global configuration instance."""
    global _config
    _config = config


# Convenience functions
def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from configuration."""
    return get_config().gemini_api_key


def get_database_url() -> str:
    """Get database URL from configuration."""
    return get_config().database_url


def validate_config() -> tuple[bool, list[str]]:
    """Validate current configuration and return (is_valid, error_messages)."""
    config = get_config()
    errors = []
    
    if not config.gemini_api_key:
        errors.append("Gemini API key is required. Set AUTOGT_GEMINI_API_KEY environment variable.")
    
    if config.max_file_size_mb <= 0:
        errors.append("Maximum file size must be positive.")
        
    if config.single_analysis_timeout_seconds <= 0:
        errors.append("Single analysis timeout must be positive.")
        
    if config.full_model_timeout_seconds <= 0:
        errors.append("Full model timeout must be positive.")
    
    return len(errors) == 0, errors