# core/config.py

from typing import Dict, List, Optional, Union, Any
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
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

class AgentConfig(BaseSettings):
    coder: str = "meta-llama/CodeLlama-13b-hf"
    researcher: str = "meta-llama/CodeLlama-13b-Instruct-hf"
    analyst: str = "meta-llama/CodeLlama-13b-Python-hf"
    creative: str = "gpt-4"

class CodeLlamaConfig(BaseSettings):
    model_variant: str = "code-llama-13b"
    quantization: str = "4bit"
    max_memory_gb: int = 12
    context_length: int = 16384
    prefer_for_coding: bool = True

class PrioritizationConfig(BaseSettings):
    frequency_weight: float = 0.3
    recency_weight: float = 0.4
    importance_weight: float = 0.3

class PrivacyZonesConfig(BaseSettings):
    private: bool = True
    shared: bool = True
    public: bool = True

class LLMConfig(BaseSettings):
    openai_api_key: Optional[str] = None
    base_model: str = "meta-llama/CodeLlama-13b-hf"
    local_model_path: str = "/home/chris-litkei/projects/axis/models/CodeLlama-13b-hf"
    default_model: str = "code-llama-13b"
    fallback_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    temperature: float = 0.1
    model_name: str = "CodeLlama-13b-hf"
    context_window: int = 16384
    auto_load_offline: bool = True
    prefer_local_models: bool = True
    gpu_memory_limit: float = 0.8
    torch_compile: bool = True
    use_cache: bool = True
    low_cpu_mem_usage: bool = True
    use_openai_fallback: bool = True
    learning_enabled: bool = True
    auto_fine_tune: bool = True
    fine_tune_interval_hours: int = 24
    interaction_dataset_path: str = "data/interactions"
    knowledge_growth_tracking: bool = True
    fallback_models: List[str] = [
        "meta-llama/CodeLlama-13b-Instruct-hf",
        "meta-llama/CodeLlama-13b-Python-hf",
        "gpt-4"
    ]
    code_llama: CodeLlamaConfig = Field(default_factory=CodeLlamaConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)

class MemoryConfig(BaseSettings):
    vector_db_path: str = "db/vector"
    sql_db_url: str = "sqlite:///db/memory.db"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_memory_items: int = 100000
    memory_cleanup_interval: int = 3600
    encryption_key: str = ""
    long_term_retention: bool = True
    cross_session_memory: bool = True
    nonlinear_memory: bool = True
    memory_tagging: bool = True
    memory_summarization: bool = True
    memory_growth_tracking: bool = True
    memory_decay_enabled: bool = True
    memory_importance_scoring: bool = True
    prioritization: PrioritizationConfig = Field(default_factory=PrioritizationConfig)

class SecurityConfig(BaseSettings):
    secret_key: str = Field(default_factory=generate_secret_key)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    audit_trail: bool = True
    admin_action_logging: bool = True
    user_access_monitoring: bool = True
    encryption_at_rest: bool = True
    live_decryption_only: bool = True
    privacy_zones: PrivacyZonesConfig = Field(default_factory=PrivacyZonesConfig)

class AudioConfig(BaseSettings):
    sample_rate: int = 16000
    whisper_model: str = "base"
    max_audio_length: int = 300
    voice_latency_threshold: int = 300
    voice_recognition: bool = True
    text_to_speech: bool = True
    emotion_detection: bool = True
    voice_tone_adjustment: bool = True
    bpm_detection: bool = True
    chord_extraction: bool = True
    lyric_extraction: bool = True
    adaptive_processing: bool = True

class ImageConfig(BaseSettings):
    max_image_size: int = 4096
    supported_formats: List[str] = ["jpg", "png", "webp"]
    yolo_model_path: str = "models/yolo"
    image_generation: bool = True
    image_analysis: bool = True
    yolo_parsing: bool = True

class PerformanceConfig(BaseSettings):
    max_workers: int = 4
    cuda_enabled: bool = True
    batch_size: int = 32
    cache_size: int = 1024
    gpu_acceleration: bool = True
    auto_optimization: bool = True
    resource_monitoring: bool = True
    memory_cleanup: bool = True
    performance_tracking: bool = True

class UploadConfig(BaseSettings):
    max_file_size: int = 100
    allowed_extensions: List[str] = [
        ".txt", ".pdf", ".doc", ".docx", ".csv", ".json",
        ".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav",
        ".ogg", ".mp4", ".py", ".js", ".cpp", ".java"
    ]
    upload_dir: str = "uploads"
    auto_indexing: bool = True
    knowledge_extraction: bool = True
    dataset_processing: bool = True

class WebConfig(BaseSettings):
    theme: str = "dark"
    max_chat_history: int = 1000
    session_timeout: int = 3600
    enable_markdown: bool = True
    enable_code_highlighting: bool = True
    enable_math_rendering: bool = True
    copilot_layout: bool = True
    integrated_editor: bool = True
    file_versioning: bool = True
    project_organization: bool = True
    visual_reasoning: bool = True
    chain_of_thought_display: bool = True

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore', env_file=".env", case_sensitive=False)
    
    app_name: str = "Axis AI"
    debug: bool = True
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    uploads: UploadConfig = Field(default_factory=UploadConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    
    @classmethod
    def load_from_yaml(cls, yaml_path: Union[str, Path]) -> "Settings":
        """Load settings from YAML file"""
        if not os.path.exists(yaml_path):
            logger.warning(f"Config file {yaml_path} not found, using defaults")
            return cls()
            
        try:
            with open(yaml_path) as f:
                yaml_config = yaml.safe_load(f)
            
            if not yaml_config:
                logger.warning(f"Config file {yaml_path} is empty, using defaults")
                return cls()
            
            # Create instance with YAML config
            instance = cls.model_validate(yaml_config)
            logger.info(f"Loaded configuration from {yaml_path}")
            return instance
            
        except Exception as e:
            logger.error(f"Error loading config from {yaml_path}: {e}")
            logger.info("Using default configuration")
            return cls()

# Global settings instance
settings = Settings.load_from_yaml("config.yaml")
