# oconsent/storage/providers.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO, Union
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path
import ipfshttpclient
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from oconsent.utils.errors import (
    StorageError, IPFSError, IPFSConnectionError,
    IPFSPinningError, IPFSTimeoutError
)

def retry_operation(retries=3, backoff_factor=0.3):
    """Decorator for retrying operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, IPFSError) as e:
                    last_error = e
                    if attempt == retries - 1:
                        raise
                    time.sleep(backoff_factor * (2 ** attempt))
            raise last_error
        return wrapper
    return decorator

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
    """Enhanced IPFS storage provider implementation."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming
    
    def __init__(
        self,
        gateway_url: str = "https://ipfs.io",
        ipfs_node: Optional[str] = None,
        pinning_service: Optional[str] = None,
        pinning_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        max_workers: int = 4
    ):
        self.gateway_url = gateway_url.rstrip('/')
        self.ipfs_node = ipfs_node
        self.pinning_service = pinning_service
        self.pinning_key = pinning_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up connection pooling
        self.session = self._create_session()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        if ipfs_node:
            try:
                self.client = ipfshttpclient.connect(
                    ipfs_node,
                    session=self.session
                )
            except Exception as e:
                raise IPFSConnectionError(f"Failed to connect to IPFS node: {e}")
        else:
            self.client = None

    def _create_session(self) -> requests.Session:
        """Creates a session with retry and timeout configuration."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=100
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @retry_operation()
    def store(self, data: bytes, **kwargs) -> str:
        """Stores data on IPFS with retries and error handling."""
        try:
            if self.client:
                # Store using local node
                result = self.client.add_bytes(
                    data,
                    pin=True,
                    **kwargs
                )
                ipfs_hash = result['Hash']
            else:
                # Store using gateway
                files = {'file': data}
                response = self.session.post(
                    f"{self.gateway_url}/api/v0/add",
                    files=files,
                    timeout=self.timeout
                )
                response.raise_for_status()
                ipfs_hash = response.json()['Hash']

            # Asynchronously pin if pinning service is configured
            if self.pinning_service and self.pinning_key:
                self.executor.submit(self._pin_hash, ipfs_hash)

            return f"ipfs://{ipfs_hash}"
            
        except requests.exceptions.Timeout:
            raise IPFSTimeoutError("IPFS storage operation timed out")
        except Exception as e:
            raise IPFSError(f"Failed to store data on IPFS: {e}")

    @retry_operation()
    def retrieve(self, reference: str) -> bytes:
        """Retrieves data from IPFS with streaming support."""
        if not reference.startswith('ipfs://'):
            raise ValueError("Invalid IPFS reference")
            
        ipfs_hash = reference[7:]
        
        try:
            if self.client:
                return self.client.cat(ipfs_hash)
            else:
                response = self.session.get(
                    f"{self.gateway_url}/ipfs/{ipfs_hash}",
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                # Stream response content
                chunks = []
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        chunks.append(chunk)
                return b''.join(chunks)
                
        except requests.exceptions.Timeout:
            raise IPFSTimeoutError("IPFS retrieval operation timed out")
        except Exception as e:
            raise IPFSError(f"Failed to retrieve data from IPFS: {e}")

    @retry_operation()
    def delete(self, reference: str) -> bool:
        """'Deletes' data from IPFS (unpins it) with retries."""
        if not reference.startswith('ipfs://'):
            raise ValueError("Invalid IPFS reference")
            
        ipfs_hash = reference[7:]
        
        try:
            if self.client:
                self.client.pin.rm(ipfs_hash)
                return True
                
            if self.pinning_service and self.pinning_key:
                return self._unpin_hash(ipfs_hash)
                
            return False
            
        except Exception as e:
            raise IPFSError(f"Failed to unpin data from IPFS: {e}")

    @retry_operation(retries=2)
    def _pin_hash(self, ipfs_hash: str) -> bool:
        """Pins an IPFS hash using the configured pinning service."""
        try:
            headers = {
                'Authorization': f'Bearer {self.pinning_key}',
                'Content-Type': 'application/json'
            }
            
            # Support for different pinning services
            if 'pinata' in self.pinning_service.lower():
                data = {'hashToPin': ipfs_hash}
            else:
                data = {'cid': ipfs_hash}
                
            response = self.session.post(
                f"{self.pinning_service}/pin/{ipfs_hash}",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if not response.ok:
                raise IPFSPinningError(f"Failed to pin hash: {response.text}")
                
            return True
            
        except requests.exceptions.Timeout:
            raise IPFSTimeoutError("Pinning operation timed out")
        except Exception as e:
            raise IPFSPinningError(f"Failed to pin hash: {e}")

    @retry_operation(retries=2)
    def _unpin_hash(self, ipfs_hash: str) -> bool:
        """Unpins an IPFS hash with retries."""
        try:
            headers = {
                'Authorization': f'Bearer {self.pinning_key}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.delete(
                f"{self.pinning_service}/pin/{ipfs_hash}",
                headers=headers,
                timeout=self.timeout
            )
            
            if not response.ok:
                raise IPFSPinningError(f"Failed to unpin hash: {response.text}")
                
            return True
            
        except requests.exceptions.Timeout:
            raise IPFSTimeoutError("Unpinning operation timed out")
        except Exception as e:
            raise IPFSPinningError(f"Failed to unpin hash: {e}")

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'client') and self.client:
            self.client.close()
            