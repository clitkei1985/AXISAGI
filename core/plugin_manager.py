import os
import json
import importlib.util
import logging
from fastapi import FastAPI
from typing import Dict

logger = logging.getLogger("axis.plugin_manager")
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler("db/audit.log")
ch.setFormatter(logging.Formatter("%(asctime)s | PLUGIN_MANAGER | %(levelname)s | %(message)s"))
logger.addHandler(ch)

class PluginManager:
    """
    Discover, load, enable/disable, and unload plugins dynamically.
    Plugins live under /plugins and each must implement a `register(app: FastAPI)` function.
    """

    loaded_plugins: Dict[str, object] = {}

    @classmethod
    def load_plugins(cls, app: FastAPI):
        """
        Read plugins/config.json to see which plugins to load.
        Then import each enabled plugin and call its `register(app)` if defined.
        """
        cfg_path = os.path.join(os.getcwd(), os.getenv("AXIS_PLUGINS_CONFIG", "plugins/config.json"))
        if not os.path.exists(cfg_path):
            logger.warning(f"Plugins config not found at {cfg_path}. Skipping plugin load.")
            return

        with open(cfg_path, "r") as f:
            try:
                plugin_cfg = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {cfg_path}.")
                return

        for plugin_name, enabled in plugin_cfg.items():
            plugin_file = os.path.join(os.getcwd(), "plugins", f"{plugin_name}.py")
            if enabled and os.path.isfile(plugin_file):
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "register"):
                        mod.register(app)
                        cls.loaded_plugins[plugin_name] = mod
                        logger.info(f"Loaded plugin '{plugin_name}' and called register().")
                    else:
                        logger.warning(f"Plugin '{plugin_name}.py' has no register(app) function.")
                except Exception as e:
                    logger.exception(f"Failed to load plugin '{plugin_name}': {e}")
            else:
                logger.info(f"Plugin '{plugin_name}' is disabled or file not found.")

    @classmethod
    def list_plugins(cls) -> Dict[str, object]:
        """Return currently loaded plugin modules."""
        return dict(cls.loaded_plugins)

    @classmethod
    def toggle_plugin(cls, plugin_name: str, enable: bool) -> None:
        """
        Enable or disable a plugin. Update config.json accordingly.
        On enabling, load it immediately; on disabling, unload (if loaded).
        """
        cfg_path = os.path.join(os.getcwd(), os.getenv("AXIS_PLUGINS_CONFIG", "plugins/config.json"))
        if not os.path.exists(cfg_path):
            raise FileNotFoundError(f"{cfg_path} does not exist.")

        with open(cfg_path, "r") as f:
            plugin_cfg = json.load(f)

        if plugin_name not in plugin_cfg:
            raise KeyError(f"Plugin '{plugin_name}' not in config.json.")

        plugin_cfg[plugin_name] = enable
        with open(cfg_path, "w") as f:
            json.dump(plugin_cfg, f, indent=2)

        if enable:
            # load it
            plugin_file = os.path.join(os.getcwd(), "plugins", f"{plugin_name}.py")
            if os.path.isfile(plugin_file):
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "register"):
                    # We assume 'app' is globally accessible or passed in another way
                    # In practice, toggle should be called within an admin endpoint 
                    # that has access to the FastAPI `app` object.
                    # e.g. PluginManager.loaded_plugins[plugin_name] = mod
                    logger.info(f"Plugin '{plugin_name}' enabled in config.json.")
                else:
                    logger.warning(f"Plugin '{plugin_name}' has no register() method.")
            else:
                logger.error(f"Plugin file not found for '{plugin_name}'.")
        else:
            # disable: if loaded, remove it
            if plugin_name in cls.loaded_plugins:
                del cls.loaded_plugins[plugin_name]
            logger.info(f"Plugin '{plugin_name}' disabled in config.json.")

    @classmethod
    def install_plugin(cls, plugin_name: str, source_code: str) -> None:
        """
        Write a new plugin file under /plugins, add it to config.json enabled, and load it.
        """
        plugins_dir = os.path.join(os.getcwd(), "plugins")
        if not os.path.isdir(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)

        plugin_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        with open(plugin_path, "w") as f:
            f.write(source_code)

        # Update config
        cfg_path = os.path.join(os.getcwd(), os.getenv("AXIS_PLUGINS_CONFIG", "plugins/config.json"))
        if not os.path.exists(cfg_path):
            with open(cfg_path, "w") as f:
                json.dump({plugin_name: True}, f, indent=2)
        else:
            with open(cfg_path, "r") as f:
                plugin_cfg = json.load(f)
            plugin_cfg[plugin_name] = True
            with open(cfg_path, "w") as f:
                json.dump(plugin_cfg, f, indent=2)

        logger.info(f"Installed new plugin '{plugin_name}'.")
        # Optionally: auto-load it (needs the FastAPI app instance context).

