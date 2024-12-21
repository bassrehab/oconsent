import pytest
import requests
from unittest.mock import Mock, patch, call
import ipfshttpclient
from requests.exceptions import Timeout, ConnectionError
import time

from oconsent.storage.providers import IPFSStorageProvider
from oconsent.utils.errors import (
    IPFSError, IPFSConnectionError, IPFSTimeoutError, IPFSPinningError
)

@pytest.fixture
def mock_session():
    with patch('requests.Session') as mock:
        session = Mock()
        mock.return_value = session
        yield session

@pytest.fixture
def ipfs_provider(mock_session):
    provider = IPFSStorageProvider(
        gateway_url="https://ipfs.example.com",
        pinning_service="https://pinning.example.com",
        pinning_key="test_key",
        timeout=5,
        max_retries=2
    )
    return provider

class TestIPFSStorageProvider:
    def test_init_with_node(self):
        """Test initialization with IPFS node"""
        with patch('ipfshttpclient.connect') as mock_connect:
            provider = IPFSStorageProvider(ipfs_node="localhost:5001")
            assert provider.client is not None
            mock_connect.assert_called_once()

    def test_init_node_failure(self):
        """Test handling of IPFS node connection failure"""
        with patch('ipfshttpclient.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(IPFSConnectionError):
                IPFSStorageProvider(ipfs_node="localhost:5001")

    def test_store_success(self, ipfs_provider, mock_session):
        """Test successful data storage"""
        mock_session.post.return_value.ok = True
        mock_session.post.return_value.json.return_value = {'Hash': 'QmTest123'}

        result = ipfs_provider.store(b"test data")
        assert result == "ipfs://QmTest123"
        mock_session.post.assert_called_once()

    def test_store_with_retries(self, ipfs_provider, mock_session):
        """Test retry behavior on temporary failures"""
        mock_session.post.side_effect = [
            ConnectionError("Temporary failure"),
            {'Hash': 'QmTest123'}
        ]
        mock_session.post.return_value.ok = True
        mock_session.post.return_value.json.return_value = {'Hash': 'QmTest123'}

        result = ipfs_provider.store(b"test data")
        assert result == "ipfs://QmTest123"
        assert mock_session.post.call_count == 2

    def test_store_timeout(self, ipfs_provider, mock_session):
        """Test handling of timeout during store operation"""
        mock_session.post.side_effect = Timeout("Request timed out")

        with pytest.raises(IPFSTimeoutError):
            ipfs_provider.store(b"test data")

    def test_store_with_pinning(self, ipfs_provider, mock_session):
        """Test storage with pinning service"""
        mock_session.post.side_effect = [
            Mock(ok=True, json=lambda: {'Hash': 'QmTest123'}),
            Mock(ok=True)
        ]

        result = ipfs_provider.store(b"test data")
        assert result == "ipfs://QmTest123"
        
        # Wait for async pinning to complete
        time.sleep(0.1)
        assert mock_session.post.call_count >= 2

    def test_retrieve_success(self, ipfs_provider, mock_session):
        """Test successful data retrieval"""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.ok = True
        mock_session.get.return_value = mock_response

        data = ipfs_provider.retrieve("ipfs://QmTest123")
        assert data == b"chunk1chunk2"
        mock_session.get.assert_called_once()

    def test_retrieve_streaming(self, ipfs_provider, mock_session):
        """Test streaming retrieval of large files"""
        large_data = b"x" * (2 * ipfs_provider.CHUNK_SIZE)
        chunks = [large_data[i:i+ipfs_provider.CHUNK_SIZE] 
                 for i in range(0, len(large_data), ipfs_provider.CHUNK_SIZE)]
        
        mock_response = Mock()
        mock_response.iter_content.return_value = chunks
        mock_response.ok = True
        mock_session.get.return_value = mock_response

        data = ipfs_provider.retrieve("ipfs://QmTest123")
        assert len(data) == len(large_data)
        assert data == large_data

    def test_retrieve_invalid_reference(self, ipfs_provider):
        """Test retrieval with invalid IPFS reference"""
        with pytest.raises(ValueError):
            ipfs_provider.retrieve("invalid://reference")

    def test_delete_success(self, ipfs_provider, mock_session):
        """Test successful deletion/unpinning"""
        mock_session.delete.return_value.ok = True

        result = ipfs_provider.delete("ipfs://QmTest123")
        assert result is True
        mock_session.delete.assert_called_once()

    def test_delete_retry_on_failure(self, ipfs_provider, mock_session):
        """Test retry on deletion failure"""
        mock_session.delete.side_effect = [
            ConnectionError("Temporary failure"),
            Mock(ok=True)
        ]

        result = ipfs_provider.delete("ipfs://QmTest123")
        assert result is True
        assert mock_session.delete.call_count == 2

    def test_pinning_service_error(self, ipfs_provider, mock_session):
        """Test handling of pinning service errors"""
        mock_session.post.return_value.ok = False
        mock_session.post.return_value.text = "Pinning failed"

        with pytest.raises(IPFSPinningError):
            ipfs_provider._pin_hash("QmTest123")

    def test_cleanup(self, ipfs_provider):
        """Test resource cleanup on deletion"""
        mock_client = Mock()
        ipfs_provider.client = mock_client
        
        del ipfs_provider
        
        # Note: This is a weak test as __del__ timing is not guaranteed
        # But it helps catch obvious issues
        assert mock_client.close.called

    @pytest.mark.parametrize("pinning_service,expected_data", [
        ("https://api.pinata.cloud", {"hashToPin": "QmTest123"}),
        ("https://api.web3.storage", {"cid": "QmTest123"}),
    ])
    def test_different_pinning_services(self, ipfs_provider, mock_session, pinning_service, expected_data):
        """Test support for different pinning services"""
        ipfs_provider.pinning_service = pinning_service
        mock_session.post.return_value.ok = True

        ipfs_provider._pin_hash("QmTest123")

        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs['json'] == expected_data

    def test_concurrent_operations(self, ipfs_provider, mock_session):
        """Test handling of concurrent operations"""
        mock_session.post.return_value.ok = True
        mock_session.post.return_value.json.return_value = {'Hash': 'QmTest123'}

        # Store multiple files concurrently
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(ipfs_provider.store, f"data{i}".encode())
                for i in range(3)
            ]
            results = [f.result() for f in futures]

        assert all(r.startswith('ipfs://') for r in results)
        assert mock_session.post.call_count == 3

    def test_session_reuse(self, ipfs_provider, mock_session):
        """Test session reuse across operations"""
        mock_session.post.return_value.ok = True
        mock_session.post.return_value.json.return_value = {'Hash': 'QmTest123'}
        mock_session.get.return_value.ok = True
        mock_session.get.return_value.iter_content.return_value = [b"data"]

        # Perform multiple operations
        ipfs_provider.store(b"test1")
        ipfs_provider.retrieve("ipfs://QmTest123")
        ipfs_provider.store(b"test2")

        # All operations should use the same session
        assert mock_session.post.call_count == 2
        assert mock_session.get.call_count == 1
        