from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO
import json
import ipfsapi
import requests
from pathlib import Path

class StorageProvider(ABC):
    """Abstract base class for storage providers."""
    
    @abstractmethod
    def store(self, data: bytes, **kwargs) -> str:
        """Stores data and returns a reference."""
        pass
    
    @abstractmethod
    def retrieve(self, reference: str) -> bytes:
        """Retrieves data using a reference."""
        pass
    
    @abstractmethod
    def delete(self, reference: str) -> bool:
        """Deletes data using a reference."""
        pass

class IPFSStorageProvider(StorageProvider):
    """IPFS storage provider implementation."""
    
    def __init__(
        self,
        gateway_url: str = "https://ipfs.io",
        ipfs_node: Optional[str] = None,
        pinning_service: Optional[str] = None,
        pinning_key: Optional[str] = None
    ):
        self.gateway_url = gateway_url.rstrip('/')
        self.ipfs_node = ipfs_node
        self.pinning_service = pinning_service
        self.pinning_key = pinning_key
        
        if ipfs_node:
            self.client = ipfsapi.connect(ipfs_node)
        else:
            self.client = None
    
    def store(self, data: bytes, **kwargs) -> str:
        """Stores data on IPFS."""
        if self.client:
            # Store using local node
            result = self.client.add_bytes(data)
            ipfs_hash = result['Hash']
        else:
            # Store using gateway
            files = {'file': data}
            response = requests.post(
                f"{self.gateway_url}/api/v0/add",
                files=files
            )
            response.raise_for_status()
            ipfs_hash = response.json()['Hash']
        
        # Pin if pinning service is configured
        if self.pinning_service and self.pinning_key:
            self._pin_hash(ipfs_hash)
        
        return f"ipfs://{ipfs_hash}"
    
    def retrieve(self, reference: str) -> bytes:
        """Retrieves data from IPFS."""
        if not reference.startswith('ipfs://'):
            raise ValueError("Invalid IPFS reference")
            
        ipfs_hash = reference[7:]
        
        if self.client:
            # Retrieve using local node
            return self.client.cat(ipfs_hash)
        else:
            # Retrieve using gateway
            response = requests.get(f"{self.gateway_url}/ipfs/{ipfs_hash}")
            response.raise_for_status()
            return response.content
    
    def delete(self, reference: str) -> bool:
        """'Deletes' data from IPFS (unpins it)."""
        if not reference.startswith('ipfs://'):
            raise ValueError("Invalid IPFS reference")
            
        ipfs_hash = reference[7:]
        
        if self.client:
            try:
                self.client.pin.rm(ipfs_hash)
                return True
            except:
                return False
                
        if self.pinning_service and self.pinning_key:
            return self._unpin_hash(ipfs_hash)
            
        return False
    
    def _pin_hash(self, ipfs_hash: str) -> bool:
        """Pins an IPFS hash using the configured pinning service."""
        headers = {'Authorization': f'Bearer {self.pinning_key}'}
        response = requests.post(
            f"{self.pinning_service}/pin/{ipfs_hash}",
            headers=headers
        )
        return response.status_code == 200
    
    def _unpin_hash(self, ipfs_hash: str) -> bool:
        """Unpins an IPFS hash from the pinning service."""
        headers = {'Authorization': f'Bearer {self.pinning_key}'}
        response = requests.delete(
            f"{self.pinning_service}/pin/{ipfs_hash}",
            headers=headers
        )
        return response.status_code == 200

class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider implementation."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def store(self, data: bytes, filename: Optional[str] = None, **kwargs) -> str:
        """Stores data in the local filesystem."""
        if not filename:
            import uuid
            filename = str(uuid.uuid4())
        
        file_path = self.base_path / filename
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return f"local://{filename}"
    
    def retrieve(self, reference: str) -> bytes:
        """Retrieves data from the local filesystem."""
        if not reference.startswith('local://'):
            raise ValueError("Invalid local reference")
            
        filename = reference[8:]
        file_path = self.base_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")
            
        with open(file_path, 'rb') as f:
            return f.read()
    
    def delete(self, reference: str) -> bool:
        """Deletes data from the local filesystem."""
        if not reference.startswith('local://'):
            raise ValueError("Invalid local reference")
            
        filename = reference[8:]
        file_path = self.base_path / filename
        
        try:
            file_path.unlink()
            return True
        except:
            return False

class StorageProviderFactory:
    """Factory for creating storage provider instances."""
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> StorageProvider:
        """Creates a storage provider based on configuration."""
        provider_type = config.get('provider', 'ipfs').lower()
        
        if provider_type == 'ipfs':
            return IPFSStorageProvider(
                gateway_url=config.get('ipfs_gateway', 'https://ipfs.io'),
                ipfs_node=config.get('ipfs_node'),
                pinning_service=config.get('pinning_service'),
                pinning_key=config.get('pinning_key')
            )
        elif provider_type == 'local':
            return LocalStorageProvider(
                base_path=config.get('base_path', '/tmp/oconsent')
            )
        else:
            raise ValueError(f"Unknown storage provider type: {provider_type}")
        