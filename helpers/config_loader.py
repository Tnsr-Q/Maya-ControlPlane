"""
Configuration Loader for Maya Control Plane Audio System

Centralized configuration management for all audio-first components.
Supports environment variable substitution and validation.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger("config_loader")


class ConfigurationLoader:
    """
    Configuration loader with environment variable support
    """
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or "config")
        self.config_cache = {}
    
    def load_config(self, config_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load configuration from YAML file with environment variable substitution
        
        Args:
            config_name: Name of configuration file (without .yaml extension)
            use_cache: Whether to use cached configuration
            
        Returns:
            Configuration dictionary
        """
        if use_cache and config_name in self.config_cache:
            return self.config_cache[config_name]
        
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Substitute environment variables
            config_content = self._substitute_env_vars(config_content)
            
            # Parse YAML
            config = yaml.safe_load(config_content)
            
            # Cache configuration
            if use_cache:
                self.config_cache[config_name] = config
            
            logger.info(f"Loaded configuration: {config_name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration {config_name}: {e}")
            return {}
    
    def get_component_config(self, config_name: str, component: str) -> Dict[str, Any]:
        """
        Get configuration for a specific component
        
        Args:
            config_name: Configuration file name
            component: Component name
            
        Returns:
            Component configuration
        """
        config = self.load_config(config_name)
        return config.get(component, {})
    
    def _substitute_env_vars(self, content: str) -> str:
        """
        Substitute environment variables in configuration content
        
        Supports format: ${VAR_NAME:-default_value}
        """
        import re
        
        def replace_env_var(match):
            var_expr = match.group(1)
            
            if ":-" in var_expr:
                var_name, default_value = var_expr.split(":-", 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, "")
        
        # Pattern to match ${VAR_NAME:-default} or ${VAR_NAME}
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_env_var, content)
    
    def validate_config(self, config: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate configuration has required keys
        
        Args:
            config: Configuration to validate
            required_keys: List of required keys (supports dot notation)
            
        Returns:
            True if valid, False otherwise
        """
        for key in required_keys:
            if not self._has_nested_key(config, key):
                logger.error(f"Missing required configuration key: {key}")
                return False
        
        return True
    
    def _has_nested_key(self, config: Dict[str, Any], key: str) -> bool:
        """Check if nested key exists in configuration"""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]
        
        return True


# Global configuration loader instance
config_loader = ConfigurationLoader()


def get_assemblyai_config() -> Dict[str, Any]:
    """Get AssemblyAI configuration"""
    return config_loader.get_component_config("audio_system", "assemblyai")


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration"""
    return config_loader.get_component_config("audio_system", "redis")


def get_maya_bridge_config() -> Dict[str, Any]:
    """Get Maya Bridge configuration"""
    return config_loader.get_component_config("audio_system", "maya_bridge")


def get_live_streaming_config() -> Dict[str, Any]:
    """Get Live Streaming configuration"""
    return config_loader.get_component_config("audio_system", "live_streaming")


def get_orchestrator_config() -> Dict[str, Any]:
    """Get Orchestrator configuration"""
    return config_loader.get_component_config("audio_system", "orchestrator")


def get_twitter_enhanced_config() -> Dict[str, Any]:
    """Get Enhanced Twitter configuration"""
    return config_loader.get_component_config("audio_system", "twitter_enhanced")


def get_cerebras_enhanced_config() -> Dict[str, Any]:
    """Get Enhanced Cerebras configuration"""
    return config_loader.get_component_config("audio_system", "cerebras_enhanced")


def get_development_config() -> Dict[str, Any]:
    """Get Development configuration"""
    return config_loader.get_component_config("audio_system", "development")


def create_component_configs() -> Dict[str, Dict[str, Any]]:
    """
    Create all component configurations for easy initialization
    
    Returns:
        Dictionary of component configurations
    """
    dev_config = get_development_config()
    use_stubs = dev_config.get('use_stubs', True)
    
    return {
        'assemblyai': {
            **get_assemblyai_config(),
            'use_stub': use_stubs
        },
        'redis': {
            **get_redis_config(),
            'use_stub': use_stubs
        },
        'maya_bridge': {
            **get_maya_bridge_config(),
            'use_stub': use_stubs
        },
        'live_streaming': {
            **get_live_streaming_config(),
            'use_stub': use_stubs
        },
        'orchestrator': {
            **get_orchestrator_config(),
            'use_stub': use_stubs
        },
        'twitter_enhanced': {
            **get_twitter_enhanced_config(),
            'use_stub': use_stubs
        },
        'cerebras_enhanced': {
            **get_cerebras_enhanced_config(),
            'use_stub': use_stubs
        }
    }


def validate_audio_system_config() -> bool:
    """
    Validate the complete audio system configuration
    
    Returns:
        True if configuration is valid
    """
    configs = create_component_configs()
    
    # Required configurations for production
    if not configs['assemblyai'].get('use_stub', True):
        if not configs['assemblyai'].get('api_key') or configs['assemblyai']['api_key'] == 'demo_key':
            logger.error("AssemblyAI API key is required for production")
            return False
    
    if not configs['redis'].get('use_stub', True):
        if not configs['redis'].get('url'):
            logger.error("Redis URL is required for production")
            return False
    
    if not configs['maya_bridge'].get('use_stub', True):
        if not configs['maya_bridge'].get('sesame_url'):
            logger.error("Sesame URL is required for Maya bridge")
            return False
    
    logger.info("Audio system configuration validation passed")
    return True


# Environment variable helpers
def set_production_env():
    """Set environment variables for production"""
    os.environ.setdefault('USE_STUBS', 'false')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('DEBUG_MODE', 'false')


def set_development_env():
    """Set environment variables for development"""
    os.environ.setdefault('USE_STUBS', 'true')
    os.environ.setdefault('LOG_LEVEL', 'DEBUG')
    os.environ.setdefault('DEBUG_MODE', 'true')


def get_api_keys_status() -> Dict[str, bool]:
    """
    Check which API keys are configured
    
    Returns:
        Status of API key configuration
    """
    return {
        'assemblyai': bool(os.getenv('ASSEMBLYAI_API_KEY')),
        'cerebras': bool(os.getenv('CEREBRAS_API_KEY')),
        'twitter_api_key': bool(os.getenv('TWITTER_API_KEY')),
        'twitter_bearer_token': bool(os.getenv('TWITTER_BEARER_TOKEN')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'redis': bool(os.getenv('REDIS_URL'))
    }


def print_configuration_status():
    """Print configuration status for debugging"""
    print("\n🔧 Maya Control Plane Configuration Status")
    print("=" * 50)
    
    # API Keys
    api_status = get_api_keys_status()
    print("\n🔑 API Keys:")
    for service, configured in api_status.items():
        status = "✅ Configured" if configured else "❌ Missing"
        print(f"   {service}: {status}")
    
    # Configuration validation
    print(f"\n⚙️ Configuration: {'✅ Valid' if validate_audio_system_config() else '❌ Invalid'}")
    
    # Development mode
    dev_config = get_development_config()
    use_stubs = dev_config.get('use_stubs', True)
    print(f"🧪 Mode: {'Development (Stubs)' if use_stubs else 'Production'}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Test configuration loading
    print_configuration_status()
    
    # Test component config creation
    configs = create_component_configs()
    print(f"\n📋 Component configs created: {list(configs.keys())}")
    
    # Test specific config loading
    assemblyai_config = get_assemblyai_config()
    print(f"🎤 AssemblyAI config loaded: {bool(assemblyai_config)}")
    
    print("\n✅ Configuration system test completed!")