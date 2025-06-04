# core/config.py

from typing import Dict, List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field
import os
import yaml
from pathlib import Path
import logging
import secrets

logger = logging.getLogger("axis.config")
logger.setLevel(logging.DEBUG)

# Ensure logs directory exists
os.makedirs("db", exist_ok=True)
fh = logging.FileHandler("db/audit.log")
fh.setFormatter(logging.Formatter("%(asctime)s | CONFIG | %(levelname)s | %(message)s"))
logger.addHandler(fh)

def generate_secret_key() -> str:
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

class LLMConfig(BaseSettings):
    openai_api_key: Optional[str] = Field(None, env="LLM_OPENAI_API_KEY")
    local_model_path: Optional[str] = Field(None, env="LLM_LOCAL_MODEL_PATH")
    use_openai_fallback: bool = Field(True, env="LLM_USE_OPENAI_FALLBACK")
    max_tokens: int = Field(2048, env="LLM_MAX_TOKENS")
    temperature: float = Field(0.7, env="LLM_TEMPERATURE")
    model_name: str = Field("gpt-4", env="LLM_MODEL_NAME")

class MemoryConfig(BaseSettings):
    vector_db_path: str = Field("db/vector", env="VECTOR_DB_PATH")
    sql_db_url: str = Field("sqlite:///db/memory.db", env="SQL_DB_URL")
    embedding_model: str = Field("all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    max_memory_items: int = Field(100000, env="MAX_MEMORY_ITEMS")
    memory_cleanup_interval: int = Field(3600, env="MEMORY_CLEANUP_INTERVAL")
    encryption_key: Optional[str] = Field(None, env="MEMORY_ENCRYPTION_KEY")

class SecurityConfig(BaseSettings):
    secret_key: str = Field(default_factory=generate_secret_key, env="SECRET_KEY")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE")
    password_min_length: int = Field(8, env="PASSWORD_MIN_LENGTH")

class AudioConfig(BaseSettings):
    sample_rate: int = Field(16000, env="AUDIO_SAMPLE_RATE")
    whisper_model: str = Field("base", env="WHISPER_MODEL")
    max_audio_length: int = Field(300, env="MAX_AUDIO_LENGTH")
    voice_latency_threshold: int = Field(300, env="VOICE_LATENCY_THRESHOLD")

class ImageConfig(BaseSettings):
    max_image_size: int = Field(4096, env="MAX_IMAGE_SIZE")
    supported_formats: List[str] = Field(["jpg", "png", "webp"], env="SUPPORTED_IMAGE_FORMATS")
    yolo_model_path: Optional[str] = Field(None, env="YOLO_MODEL_PATH")

class PerformanceConfig(BaseSettings):
    max_workers: int = Field(4, env="MAX_WORKERS")
    cuda_enabled: bool = Field(False, env="CUDA_ENABLED")
    batch_size: int = Field(32, env="BATCH_SIZE")
    cache_size: int = Field(1024, env="CACHE_SIZE_MB")

class Settings(BaseSettings):
    app_name: str = Field("Axis AI", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    base_url: str = Field("http://localhost:8000", env="BASE_URL")
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    @classmethod
    def load_from_yaml(cls, yaml_path: Union[str, Path]) -> "Settings":
        """Load settings from YAML file if it exists"""
        if not os.path.exists(yaml_path):
            logger.warning(f"Config file {yaml_path} not found, using defaults")
            return cls()
            
        try:
            with open(yaml_path) as f:
                yaml_config = yaml.safe_load(f)
            
            if not yaml_config:
                logger.warning(f"Config file {yaml_path} is empty, using defaults")
                return cls()
            
            # Process nested config sections
            env_updates = {}
            
            # Flatten nested YAML structure for environment variables
            def flatten_dict(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)
            
            flattened = flatten_dict(yaml_config)
            
            # Override environment variables with yaml values (only if not empty)
            for key, value in flattened.items():
                if value is not None and str(value).strip():  # Skip empty values
                    env_updates[key.upper()] = str(value)
            
            # Apply environment updates
            for key, value in env_updates.items():
                os.environ[key] = value
            
            logger.info(f"Loaded configuration from {yaml_path}")
            
            # Create instance after environment variables are set
            instance = cls()
            
            # Rebuild the nested config models to pick up the new environment variables
            instance.llm = LLMConfig()
            instance.memory = MemoryConfig()
            instance.security = SecurityConfig()
            instance.audio = AudioConfig()
            instance.image = ImageConfig()
            instance.performance = PerformanceConfig()
            
            return instance
            
        except Exception as e:
            logger.error(f"Error loading config from {yaml_path}: {e}")
            logger.info("Using default configuration")
            return cls()

    def save_to_yaml(self, yaml_path: Union[str, Path]) -> None:
        config_dict = self.dict()
        with open(yaml_path, 'w') as f:
            yaml.dump(config_dict, f)

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings.load_from_yaml("config.yaml")
