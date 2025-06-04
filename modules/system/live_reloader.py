import importlib
import sys
import os
import threading
import time
import logging
from typing import Dict, Set, Optional, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.config import settings
import hashlib

logger = logging.getLogger(__name__)

class ModuleReloader:
    """Live module reloading system for dynamic updates (Feature 192)"""
    
    def __init__(self):
        self.watched_modules: Dict[str, float] = {}
        self.module_hashes: Dict[str, str] = {}
        self.reload_callbacks: Dict[str, callable] = {}
        self.observer = None
        self.is_monitoring = False
        self.reload_lock = threading.Lock()
        
    def start_monitoring(self, watch_paths: Optional[list] = None):
        """Start monitoring for file changes"""
        if self.is_monitoring:
            return
            
        if not watch_paths:
            watch_paths = ['modules', 'interfaces', 'core']
            
        self.observer = Observer()
        handler = ModuleChangeHandler(self)
        
        for path in watch_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)
                logger.info(f"Monitoring {path} for changes")
        
        self.observer.start()
        self.is_monitoring = True
        logger.info("Live reloader started")
    
    def stop_monitoring(self):
        """Stop monitoring for changes"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            logger.info("Live reloader stopped")
    
    def register_callback(self, module_name: str, callback: callable):
        """Register callback for module reload"""
        self.reload_callbacks[module_name] = callback
        
    def get_module_hash(self, file_path: str) -> str:
        """Get hash of module file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def reload_module(self, module_path: str) -> bool:
        """Safely reload a Python module"""
        with self.reload_lock:
            try:
                # Convert file path to module name
                module_name = self._path_to_module_name(module_path)
                if not module_name:
                    return False
                
                # Check if module is already loaded
                if module_name not in sys.modules:
                    logger.info(f"Module {module_name} not loaded, skipping reload")
                    return False
                
                # Get current hash
                current_hash = self.get_module_hash(module_path)
                previous_hash = self.module_hashes.get(module_name)
                
                if current_hash == previous_hash:
                    return False  # No changes
                
                # Store backup reference
                old_module = sys.modules[module_name]
                
                # Reload the module
                logger.info(f"Reloading module: {module_name}")
                new_module = importlib.reload(old_module)
                
                # Update hash
                self.module_hashes[module_name] = current_hash
                
                # Execute callback if registered
                if module_name in self.reload_callbacks:
                    try:
                        self.reload_callbacks[module_name](new_module)
                    except Exception as e:
                        logger.error(f"Callback error for {module_name}: {e}")
                
                logger.info(f"Successfully reloaded: {module_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to reload {module_path}: {e}")
                return False
    
    def _path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert file path to Python module name"""
        if not file_path.endswith('.py'):
            return None
            
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        # Remove .py extension
        module_path = file_path[:-3]
        
        # Convert to module notation
        module_name = module_path.replace(os.sep, '.')
        
        # Remove leading dots
        module_name = module_name.lstrip('.')
        
        return module_name
    
    def reload_all_changed(self):
        """Reload all modules that have changed"""
        reloaded = []
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(('modules.', 'interfaces.', 'core.')):
                try:
                    module = sys.modules[module_name]
                    if hasattr(module, '__file__') and module.__file__:
                        file_path = module.__file__
                        if file_path.endswith('.py'):
                            current_hash = self.get_module_hash(file_path)
                            if current_hash != self.module_hashes.get(module_name):
                                if self.reload_module(file_path):
                                    reloaded.append(module_name)
                except Exception as e:
                    logger.error(f"Error checking {module_name}: {e}")
        
        return reloaded

class ModuleChangeHandler(FileSystemEventHandler):
    """File system event handler for module changes"""
    
    def __init__(self, reloader: ModuleReloader):
        self.reloader = reloader
        self.debounce_delay = 1.0  # Seconds
        self.pending_reloads: Dict[str, float] = {}
        
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.py'):
            return
            
        # Debounce rapid file changes
        current_time = time.time()
        self.pending_reloads[event.src_path] = current_time
        
        # Schedule reload after delay
        threading.Timer(
            self.debounce_delay,
            self._delayed_reload,
            args=[event.src_path, current_time]
        ).start()
    
    def _delayed_reload(self, file_path: str, scheduled_time: float):
        """Execute delayed reload if no newer changes"""
        if self.pending_reloads.get(file_path) == scheduled_time:
            self.reloader.reload_module(file_path)
            self.pending_reloads.pop(file_path, None)

# Singleton instance
_reloader = None

def get_reloader() -> ModuleReloader:
    """Get or create the module reloader instance"""
    global _reloader
    if _reloader is None:
        _reloader = ModuleReloader()
    return _reloader

def start_live_reloading():
    """Start live reloading system"""
    reloader = get_reloader()
    reloader.start_monitoring()
    return reloader

def stop_live_reloading():
    """Stop live reloading system"""
    reloader = get_reloader()
    reloader.stop_monitoring() 