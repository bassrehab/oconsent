
import os
import json
from typing import Dict, Any, Optional
import click
from dataclasses import dataclass

@dataclass
class EthereumConfig:
    provider_url: str
    contract_address: str
    private_key: Optional[str] = None
    chain_id: int = 1
    gas_limit: int = 6000000
    gas_price_strategy: str = "medium"

@dataclass
class SnarkConfig:
    params_path: str
    proving_key_path: Optional[str] = None
    verification_key_path: Optional[str] = None

@dataclass
class TimestampConfig:
    providers: Dict[str, bool] = None
    nist_beacon_url: str = "https://beacon.nist.gov/beacon/2.0"
    bitcoin_node_url: Optional[str] = None

@dataclass
class StorageConfig:
    provider: str = "ipfs"
    ipfs_gateway: str = "https://ipfs.io"
    pinning_service: Optional[str] = None
    pinning_key: Optional[str] = None

class Config:
    """Configuration manager for OConsent."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_prefix: str = "OCONSENT_"
    ):
        self.env_prefix = env_prefix
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Gets the default configuration file path."""
        config_dir = click.get_app_dir('oconsent')
        return os.path.join(config_dir, 'config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from file and environment variables."""
        # Default configuration
        config = {
            'ethereum': EthereumConfig(
                provider_url="http://localhost:8545",
                contract_address="",
                chain_id=1
            ),
            'snark': SnarkConfig(
                params_path="params/snark_params.json"
            ),
            'timestamp': TimestampConfig(
                providers={
                    'nist': True,
                    'bitcoin': False
                }
            ),
            'storage': StorageConfig()
        }
        
        # Load from file if exists
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                file_config = json.load(f)
                self._merge_config(config, file_config)
        
        # Override with environment variables
        self._load_env_vars(config)
        
        return config
    
    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merges override config into base config."""
        for key, value in override.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    self._merge_config(base[key], value)
                else:
                    base[key] = value
    
    def _load_env_vars(self, config: Dict) -> None:
        """Loads configuration from environment variables."""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix):].lower()
                parts = config_key.split('_')
                
                # Navigate to the correct config section
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set the value
                current[parts[-1]] = value
    
    def save(self) -> None:
        """Saves the current configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Gets a configuration value."""
        try:
            parts = key.split('.')
            value = self.config
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Sets a configuration value."""
        parts = key.split('.')
        current = self.config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        