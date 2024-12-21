import pytest
import os
import time
from typing import Generator
import ipfshttpclient
from pathlib import Path

from oconsent.storage.providers import IPFSStorageProvider
from oconsent.utils.errors import IPFSError

# Integration test configuration - override with environment variables
IPFS_NODE = os.getenv('IPFS_NODE', '/ip4/127.0.0.1/tcp/5001')
IPFS_GATEWAY = os.getenv('IPFS_GATEWAY', 'https://ipfs.io')
PINNING_SERVICE = os.getenv('IPFS_PINNING_SERVICE')  # Optional
PINNING_KEY = os.getenv('IPFS_PINNING_KEY')  # Optional

@pytest.fixture(scope="session")
def ipfs_client() -> Generator[ipfshttpclient.Client, None, None]:
    """Create a session-scoped IPFS client for testing."""
    try:
        client = ipfshttpclient.connect(IPFS_NODE)
        yield client
    finally:
        if 'client' in locals():
            client.close()

@pytest.fixture(scope="session")
def ipfs_provider() -> Generator[IPFSStorageProvider, None, None]:
    """Create a session-scoped IPFS provider for testing."""
    provider = IPFSStorageProvider(
        gateway_url=IPFS_GATEWAY,
        ipfs_node=IPFS_NODE,
        pinning_service=PINNING_SERVICE,
        pinning_key=PINNING_KEY,
        timeout=30  # Longer timeout for integration tests
    )
    yield provider
    del provider

@pytest.fixture
def test_file(tmp_path) -> Path:
    """Create a temporary test file."""
    file_path = tmp_path / "test_file.txt"
    content = b"OConsent IPFS Integration Test " + os.urandom(1024)  # 1KB random data
    file_path.write_bytes(content)
    return file_path

@pytest.fixture
def large_test_file(tmp_path) -> Path:
    """Create a large temporary test file (5MB)."""
    file_path = tmp_path / "large_test_file.txt"
    content = b"OConsent Large File Test " + os.urandom(5 * 1024 * 1024)  # 5MB random data
    file_path.write_bytes(content)
    return file_path

@pytest.mark.integration
class TestIPFSIntegration:
    def test_connect_to_node(self, ipfs_client):
        """Test connection to IPFS node."""
        version = ipfs_client.version()
        assert isinstance(version['Version'], str)

    def test_store_and_retrieve(self, ipfs_provider, test_file):
        """Test basic store and retrieve operations."""
        # Store file
        test_data = test_file.read_bytes()
        reference = ipfs_provider.store(test_data)
        assert reference.startswith('ipfs://')

        # Retrieve and verify
        retrieved_data = ipfs_provider.retrieve(reference)
        assert retrieved_data == test_data

        # Verify through IPFS gateway
        ipfs_hash = reference[7:]  # Remove 'ipfs://' prefix
        gateway_url = f"{IPFS_GATEWAY}/ipfs/{ipfs_hash}"
        import requests
        response = requests.get(gateway_url)
        assert response.content == test_data

    def test_large_file_handling(self, ipfs_provider, large_test_file):
        """Test handling of large files."""
        test_data = large_test_file.read_bytes()
        reference = ipfs_provider.store(test_data)
        
        retrieved_data = ipfs_provider.retrieve(reference)
        assert len(retrieved_data) == len(test_data)
        assert retrieved_data == test_data

    @pytest.mark.skipif(not PINNING_SERVICE or not PINNING_KEY, 
                       reason="Pinning service not configured")
    def test_pinning_service(self, ipfs_provider, test_file):
        """Test pinning service integration."""
        test_data = test_file.read_bytes()
        reference = ipfs_provider.store(test_data)
        
        # Wait for async pinning to complete
        time.sleep(5)
        
        # Verify pin (implementation depends on pinning service)
        ipfs_hash = reference[7:]
        # Example for Pinata:
        if 'pinata' in PINNING_SERVICE.lower():
            import requests
            headers = {'Authorization': f'Bearer {PINNING_KEY}'}
            response = requests.get(
                f"{PINNING_SERVICE}/data/pinList?status=pinned&hashContains={ipfs_hash}",
                headers=headers
            )
            assert response.ok
            data = response.json()
            assert any(pin['ipfs_pin_hash'] == ipfs_hash for pin in data['rows'])

    def test_concurrent_operations(self, ipfs_provider, test_file):
        """Test concurrent store/retrieve operations."""
        test_data = test_file.read_bytes()
        
        from concurrent.futures import ThreadPoolExecutor
        
        # Store multiple copies concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(ipfs_provider.store, test_data)
                for _ in range(3)
            ]
            references = [f.result() for f in futures]
        
        # Retrieve concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(ipfs_provider.retrieve, ref)
                for ref in references
            ]
            results = [f.result() for f in futures]
        
        assert all(data == test_data for data in results)

    def test_error_recovery(self, ipfs_provider, test_file):
        """Test recovery from network errors."""
        test_data = test_file.read_bytes()
        
        # Test with intentionally bad gateway first
        original_gateway = ipfs_provider.gateway_url
        ipfs_provider.gateway_url = "http://nonexistent.example.com"
        
        with pytest.raises(IPFSError):
            ipfs_provider.store(test_data)
        
        # Restore gateway and verify operation succeeds
        ipfs_provider.gateway_url = original_gateway
        reference = ipfs_provider.store(test_data)
        retrieved_data = ipfs_provider.retrieve(reference)
        assert retrieved_data == test_data

    def test_long_running_operations(self, ipfs_provider, large_test_file):
        """Test behavior during long-running operations."""
        # First, simulate network latency
        import time
        test_data = large_test_file.read_bytes()
        
        start_time = time.time()
        reference = ipfs_provider.store(test_data)
        store_duration = time.time() - start_time
        
        start_time = time.time()
        retrieved_data = ipfs_provider.retrieve(reference)
        retrieve_duration = time.time() - start_time
        
        assert retrieved_data == test_data
        
        # Log performance metrics
        print(f"\nPerformance metrics for 5MB file:")
        print(f"Store duration: {store_duration:.2f}s")
        print(f"Retrieve duration: {retrieve_duration:.2f}s")
        print(f"Store throughput: {len(test_data)/store_duration/1024/1024:.2f} MB/s")
        print(f"Retrieve throughput: {len(test_data)/retrieve_duration/1024/1024:.2f} MB/s")
        