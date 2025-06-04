from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    author: str
    enabled: bool
    loaded_at: str
    file_path: str
    config: Dict[str, Any]
    last_error: Optional[str]
    available_actions: List[str]
    config_schema: Dict[str, Any]

class PluginUpload(BaseModel):
    filename: str
    content: str  # Base64 encoded plugin file
    auto_enable: bool = False

class PluginAction(BaseModel):
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class PluginActionResult(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PluginConfig(BaseModel):
    config: Dict[str, Any]

class PluginStatus(BaseModel):
    name: str
    enabled: bool
    last_error: Optional[str]
    uptime: Optional[float]  # seconds since enabled

class PluginInstallRequest(BaseModel):
    plugin_url: Optional[str] = None  # URL to download plugin
    plugin_data: Optional[str] = None  # Base64 encoded plugin data
    auto_enable: bool = False
    config: Optional[Dict[str, Any]] = None

class PluginInstallResponse(BaseModel):
    success: bool
    plugin_name: Optional[str] = None
    message: str
    installed_at: datetime = Field(default_factory=datetime.utcnow)

class HookRegistration(BaseModel):
    hook_name: str
    plugin_name: str
    callback_action: str  # The action to call on the plugin

class PluginListResponse(BaseModel):
    plugins: Dict[str, PluginInfo]
    total_count: int
    enabled_count: int
    disabled_count: int 