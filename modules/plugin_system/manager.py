import os
import sys
import importlib
import inspect
import asyncio
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import logging
from datetime import datetime
import json
from abc import ABC, abstractmethod

from core.config import settings
from core.database import Session, get_db

logger = logging.getLogger(__name__)

class PluginInterface(ABC):
    """Base interface that all plugins must implement."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """Plugin author."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Any:
        """Execute a plugin action."""
        pass
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions this plugin supports."""
        return []
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this plugin."""
        return {}

class PluginMetadata:
    def __init__(self, plugin: PluginInterface, file_path: str):
        self.plugin = plugin
        self.file_path = file_path
        self.name = plugin.name
        self.version = plugin.version
        self.description = plugin.description
        self.author = plugin.author
        self.loaded_at = datetime.utcnow()
        self.enabled = False
        self.config = {}
        self.last_error = None

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.plugin_directory = Path("plugins")
        self.hooks: Dict[str, List[Callable]] = {}
        self.security_sandbox = settings.plugins.enable_sandbox if hasattr(settings, 'plugins') else True
        
        # Create plugins directory if it doesn't exist
        self.plugin_directory.mkdir(exist_ok=True)
    
    async def load_plugin(self, plugin_path: str) -> bool:
        """Load a single plugin from file path."""
        try:
            plugin_file = Path(plugin_path)
            if not plugin_file.exists():
                raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
            # Add plugin directory to Python path
            plugin_dir = plugin_file.parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            # Import the plugin module
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class that implements PluginInterface
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                raise ValueError("No valid plugin class found in module")
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            
            # Validate plugin
            await self._validate_plugin(plugin_instance)
            
            # Create metadata
            metadata = PluginMetadata(plugin_instance, plugin_path)
            
            # Load configuration if exists
            config_file = plugin_dir / f"{module_name}.config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    metadata.config = json.load(f)
            
            # Initialize plugin
            init_success = await plugin_instance.initialize(metadata.config)
            if not init_success:
                raise RuntimeError("Plugin initialization failed")
            
            # Register plugin
            self.plugins[plugin_instance.name] = metadata
            metadata.enabled = True
            
            logger.info(f"Successfully loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return False
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """Load all plugins from the plugins directory."""
        results = {}
        
        for plugin_file in self.plugin_directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            plugin_name = plugin_file.stem
            results[plugin_name] = await self.load_plugin(str(plugin_file))
        
        return results
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin."""
        if plugin_name not in self.plugins:
            return False
        
        try:
            metadata = self.plugins[plugin_name]
            
            # Cleanup plugin
            await metadata.plugin.cleanup()
            
            # Remove from registry
            del self.plugins[plugin_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name not in self.plugins:
            return False
        
        metadata = self.plugins[plugin_name]
        if metadata.enabled:
            return True
        
        try:
            # Re-initialize plugin
            await metadata.plugin.initialize(metadata.config)
            metadata.enabled = True
            metadata.last_error = None
            
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_name}: {e}")
            metadata.last_error = str(e)
            return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if plugin_name not in self.plugins:
            return False
        
        metadata = self.plugins[plugin_name]
        if not metadata.enabled:
            return True
        
        try:
            await metadata.plugin.cleanup()
            metadata.enabled = False
            
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_name}: {e}")
            return False
    
    async def execute_plugin_action(
        self, 
        plugin_name: str, 
        action: str, 
        **kwargs
    ) -> Any:
        """Execute an action on a specific plugin."""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        metadata = self.plugins[plugin_name]
        if not metadata.enabled:
            raise RuntimeError(f"Plugin {plugin_name} is disabled")
        
        try:
            # Execute in sandbox if enabled
            if self.security_sandbox:
                return await self._execute_sandboxed(metadata.plugin, action, **kwargs)
            else:
                return await metadata.plugin.execute(action, **kwargs)
                
        except Exception as e:
            logger.error(f"Plugin {plugin_name} action {action} failed: {e}")
            metadata.last_error = str(e)
            raise
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    async def trigger_hook(self, hook_name: str, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook."""
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        result = await callback(**kwargs)
                    else:
                        result = callback(**kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook {hook_name} callback failed: {e}")
        return results
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin."""
        if plugin_name not in self.plugins:
            return None
        
        metadata = self.plugins[plugin_name]
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "enabled": metadata.enabled,
            "loaded_at": metadata.loaded_at.isoformat(),
            "file_path": metadata.file_path,
            "config": metadata.config,
            "last_error": metadata.last_error,
            "available_actions": metadata.plugin.get_available_actions(),
            "config_schema": metadata.plugin.get_config_schema()
        }
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded plugins."""
        return {
            name: self.get_plugin_info(name)
            for name in self.plugins.keys()
        }
    
    async def update_plugin_config(
        self, 
        plugin_name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """Update plugin configuration."""
        if plugin_name not in self.plugins:
            return False
        
        metadata = self.plugins[plugin_name]
        metadata.config.update(config)
        
        # Save configuration to file
        config_file = Path(metadata.file_path).parent / f"{plugin_name}.config.json"
        with open(config_file, 'w') as f:
            json.dump(metadata.config, f, indent=2)
        
        # Restart plugin if enabled
        if metadata.enabled:
            await self.disable_plugin(plugin_name)
            await self.enable_plugin(plugin_name)
        
        return True
    
    async def _validate_plugin(self, plugin: PluginInterface) -> None:
        """Validate plugin implementation."""
        required_methods = ['initialize', 'cleanup', 'execute']
        required_properties = ['name', 'version', 'description', 'author']
        
        for method in required_methods:
            if not hasattr(plugin, method):
                raise ValueError(f"Plugin missing required method: {method}")
        
        for prop in required_properties:
            if not hasattr(plugin, prop):
                raise ValueError(f"Plugin missing required property: {prop}")
    
    async def _execute_sandboxed(
        self, 
        plugin: PluginInterface, 
        action: str, 
        **kwargs
    ) -> Any:
        """Execute plugin action in a security sandbox."""
        # Basic sandboxing - in production, use more robust isolation
        try:
            # Set execution timeout
            return await asyncio.wait_for(
                plugin.execute(action, **kwargs),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError("Plugin execution timed out")

# Singleton instance
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Get or create the PluginManager singleton instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

async def initialize_plugin_system():
    """Initialize the plugin system on startup"""
    try:
        logger.info("Initializing plugin system...")
        plugin_manager = get_plugin_manager()
        
        # Load all available plugins
        results = await plugin_manager.load_all_plugins()
        
        loaded_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Plugin system initialized: {loaded_count}/{total_count} plugins loaded")
    except Exception as e:
        logger.error(f"Plugin system initialization failed: {e}")
        raise
