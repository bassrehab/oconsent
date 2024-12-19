# tests/unit/test_storage.py

import pytest
from unittest.mock import Mock, patch
from oconsent.storage.providers import StorageProvider, IPFSStorageProvider, LocalStorageProvider
from oconsent.utils.errors import StorageError

@pytest.fixture
def ipfs_storage():
    with patch('ipfsapi.connect') as mock_connect:
        provider = IPFSStorageProvider(
            gateway_url="https://ipfs.io",
            ipfs_node=None
        )
        return provider

@pytest.fixture
def local_storage(tmp_path):
    return LocalStorageProvider(base_path=str(tmp_path))

class TestIPFSStorage:
    def test_store_data(self, ipfs_storage):
        """Test storing data on IPFS"""
        test_data = b"test data"
        
        # Mock IPFS response
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'Hash': 'QmTest'}
            
            reference = ipfs_storage.store(test_data)
            assert reference.startswith('ipfs://')
            assert 'QmTest' in reference

    def test_retrieve_data(self, ipfs_storage):
        """Test retrieving data from IPFS"""
        test_reference = 'ipfs://QmTest'
        
        # Mock IPFS response
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = b"test data"
            
            data = ipfs_storage.retrieve(test_reference)
            assert data == b"test data"

    def test_delete_data(self, ipfs_storage):
        """Test deleting data from IPFS"""
        test_reference = 'ipfs://QmTest'
        
        # Mock IPFS response
        with patch('requests.delete') as mock_delete:
            mock_delete.return_value.status_code = 200
            
            result = ipfs_storage.delete(test_reference)
            assert result is True

class TestLocalStorage:
    def test_store_data(self, local_storage):
        """Test storing data locally"""
        test_data = b"test data"
        reference = local_storage.store(test_data)
        
        assert reference.startswith('local://')
        stored_data = local_storage.retrieve(reference)
        assert stored_data == test_data

    def test_retrieve_nonexistent(self, local_storage):
        """Test retrieving non-existent data"""
        with pytest.raises(FileNotFoundError):
            local_storage.retrieve('local://nonexistent')

    def test_delete_data(self, local_storage):
        """Test deleting local data"""
        test_data = b"test data"
        reference = local_storage.store(test_data)
        
        assert local_storage.delete(reference) is True
        with pytest.raises(FileNotFoundError):
            local_storage.retrieve(reference)
            