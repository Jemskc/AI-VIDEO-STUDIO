"""
Plugin System - Dynamic plugin registration for AI providers.

Allows new AI models to be added as plugins without modifying core code.
"""

import importlib
import logging
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json

from app.providers.base import BaseProvider, ProviderRegistry

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Information about a registered plugin."""
    name: str
    version: str
    provider_type: str
    description: str
    author: str
    path: str
    installed_at: datetime
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "provider_type": self.provider_type,
            "description": self.description,
            "author": self.author,
            "path": self.path,
            "installed_at": self.installed_at.isoformat(),
            "enabled": self.enabled,
            "metadata": self.metadata or {}
        }


class PluginManager:
    """
    Manages AI provider plugins.
    
    Features:
    - Dynamic plugin discovery
    - Plugin registration/unregistration
    - Version tracking
    - Enable/disable plugins
    """
    
    def __init__(self, plugins_dir: str = "app/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_instances: Dict[str, BaseProvider] = {}
    
    async def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory.
        
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return discovered
        
        # Look for plugin modules
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check for plugin manifest
                manifest_path = item / "plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        
                        plugin_name = manifest.get("name", item.name)
                        discovered.append(plugin_name)
                        logger.info(f"Discovered plugin: {plugin_name}")
                    except Exception as e:
                        logger.error(f"Error reading manifest for {item.name}: {e}")
            
            elif item.is_file() and item.name.endswith(".py") and not item.name.startswith("_"):
                # Single-file plugin
                plugin_name = item.stem
                discovered.append(plugin_name)
                logger.info(f"Discovered single-file plugin: {plugin_name}")
        
        return discovered
    
    async def load_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Load and register a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            PluginInfo if successful, None otherwise
        """
        try:
            # Try to import the plugin module
            module = importlib.import_module(f"app.plugins.{plugin_name}")
            
            # Look for plugin manifest or default metadata
            manifest_path = self.plugins_dir / plugin_name / "plugin.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
            else:
                manifest = {
                    "name": plugin_name,
                    "version": "1.0.0",
                    "provider_type": "custom",
                    "description": f"Plugin: {plugin_name}",
                    "author": "Unknown"
                }
            
            # Look for provider class in module
            provider_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) 
                    and issubclass(attr, BaseProvider) 
                    and attr != BaseProvider
                ):
                    provider_class = attr
                    break
            
            if not provider_class:
                logger.warning(f"No provider class found in plugin {plugin_name}")
                return None
            
            # Create plugin info
            plugin_info = PluginInfo(
                name=manifest.get("name", plugin_name),
                version=manifest.get("version", "1.0.0"),
                provider_type=manifest.get("provider_type", "custom"),
                description=manifest.get("description", ""),
                author=manifest.get("author", "Unknown"),
                path=str(self.plugins_dir / plugin_name),
                installed_at=datetime.utcnow(),
                metadata=manifest
            )
            
            # Instantiate and register provider
            provider = provider_class()
            ProviderRegistry.register(provider)
            
            self._plugins[plugin_name] = plugin_info
            self._plugin_instances[plugin_name] = provider
            
            logger.info(f"Loaded plugin: {plugin_name} ({plugin_info.provider_type})")
            return plugin_info
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            return None
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload and unregister a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if successful, False otherwise
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin_info = self._plugins[plugin_name]
        provider = self._plugin_instances.get(plugin_name)
        
        # Shutdown provider
        if provider:
            try:
                await provider.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down provider {plugin_name}: {e}")
        
        # Unregister from provider registry
        ProviderRegistry.unregister(plugin_info.provider_type)
        
        # Remove from internal tracking
        del self._plugins[plugin_name]
        if plugin_name in self._plugin_instances:
            del self._plugin_instances[plugin_name]
        
        logger.info(f"Unloaded plugin: {plugin_name}")
        return True
    
    async def load_all_plugins(self) -> Dict[str, PluginInfo]:
        """Load all available plugins."""
        discovered = await self.discover_plugins()
        loaded = {}
        
        for plugin_name in discovered:
            plugin_info = await self.load_plugin(plugin_name)
            if plugin_info:
                loaded[plugin_name] = plugin_info
        
        logger.info(f"Loaded {len(loaded)} plugins")
        return loaded
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin."""
        return self._plugins.get(plugin_name)
    
    def get_provider(self, plugin_name: str) -> Optional[BaseProvider]:
        """Get the provider instance for a plugin."""
        return self._plugin_instances.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        return [info.to_dict() for info in self._plugins.values()]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].enabled = False
            return True
        return False


# Global singleton instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def initialize_plugin_manager(plugins_dir: str = "app/plugins") -> PluginManager:
    """Initialize and load all plugins."""
    global _plugin_manager
    _plugin_manager = PluginManager(plugins_dir)
    await _plugin_manager.load_all_plugins()
    return _plugin_manager
