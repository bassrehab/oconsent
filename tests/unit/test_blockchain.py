import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from web3 import Web3
from eth_typing import Address
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.utils.errors import BlockchainError

# Mock contract ABI
MOCK_ABI = {
    "abi": [
        {
            "inputs": [
                {"name": "id", "type": "string"},
                {"name": "data", "type": "tuple", "components": [
                    {"name": "id", "type": "string"},
                    {"name": "subject_id", "type": "string"},
                    {"name": "processor_id", "type": "string"},
                    {"name": "purposes", "type": "tuple[]"},
                    {"name": "valid_from", "type": "uint256"},
                    {"name": "valid_until", "type": "uint256"},
                    {"name": "metadata", "type": "string"},
                    {"name": "status", "type": "string"},
                    {"name": "proof_id", "type": "string"},
                    {"name": "timestamp_proof", "type": "string"}
                ]}
            ],
            "name": "storeAgreement",
            "outputs": [{"type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
}

@pytest.fixture
def mock_contract():
    contract = Mock()
    
    # Setup storeAgreement
    store_func = Mock()
    store_func.build_transaction.return_value = {
        'from': '0x0000000000000000000000000000000000000000',
        'nonce': 1
    }
    contract.functions.storeAgreement.return_value = store_func
    
    # Setup getAgreement
    get_func = Mock()
    get_func.call.return_value = {
        'id': 'test-id',
        'subject_id': 'test-subject',
        'processor_id': 'test-processor',
        'purposes': [],
        'valid_from': 1234567890,
        'valid_until': 0,
        'metadata': {},
        'status': 'active',
        'proof_id': 'test-proof',
        'timestamp_proof': 'test-timestamp'
    }
    contract.functions.getAgreement.return_value = get_func
    
    return contract

@pytest.fixture
def ethereum_client(mock_contract):
    with patch('web3.Web3.HTTPProvider'), \
         patch.object(EthereumClient, '__init__', return_value=None) as mock_init:
        
        client = EthereumClient(
            provider_url="http://localhost:8545",
            contract_address="0x0000000000000000000000000000000000000000",
            private_key="0x0000000000000000000000000000000000000000000000000000000000000000",
            contract_abi=MOCK_ABI
        )
        
        # Setup client attributes manually
        client.web3 = Mock()
        client.web3.eth = Mock()
        client.web3.eth.contract.return_value = mock_contract
        client.web3.eth.account = Mock()
        client.web3.eth.get_transaction_count = Mock(return_value=1)
        client.web3.eth.send_raw_transaction = Mock(return_value=b'tx_hash')
        client.web3.eth.wait_for_transaction_receipt = Mock(
            return_value=Mock(transactionHash=b'tx_hash')
        )
        
        # Setup account methods
        account = Mock()
        account.address = "0x0000000000000000000000000000000000000000"
        client.web3.eth.account.from_key = Mock(return_value=account)
        client.web3.eth.account.sign_transaction = Mock(
            return_value=Mock(rawTransaction=b'raw_tx')
        )
        
        # Set other required attributes
        client.contract = mock_contract
        client.contract_address = "0x0000000000000000000000000000000000000000"
        client.private_key = "0x0000000000000000000000000000000000000000000000000000000000000000"
        client.contract_abi = MOCK_ABI['abi']
        
        return client

class TestEthereumClient:
    def test_store_agreement(self, ethereum_client):
        """Test storing agreement on blockchain"""
        # Setup mock agreement
        agreement = Mock()
        agreement.id = "test-id"
        agreement.subject_id = "test-subject"
        agreement.processor_id = "test-processor"
        agreement.purposes = []
        agreement.valid_from = datetime.utcnow()
        agreement.valid_until = None
        agreement.metadata = {}
        agreement.status = "active"
        agreement.proof_id = "test-proof"
        agreement.timestamp_proof = "test-timestamp"

        tx_hash = ethereum_client.store_agreement(agreement)
        assert isinstance(tx_hash, str)
        assert tx_hash == "0x7478686173680000000000000000000000000000000000000000000000000000"

    def test_get_agreement(self, ethereum_client):
        """Test retrieving agreement from blockchain"""
        agreement = ethereum_client.get_agreement("test-id")
        assert agreement is not None
        assert agreement.id == 'test-id'
        assert agreement.subject_id == 'test-subject'

    def test_error_handling(self, ethereum_client):
        """Test error handling"""
        ethereum_client.contract.functions.getAgreement.return_value.call.side_effect = Exception("Web3 error")
        with pytest.raises(BlockchainError):
            ethereum_client.get_agreement("test-id")

    def test_update_agreement(self, ethereum_client):
        """Test updating agreement on blockchain"""
        agreement = Mock()
        agreement.id = "test-id"
        agreement.subject_id = "test-subject"
        agreement.processor_id = "test-processor"
        agreement.purposes = []
        agreement.valid_from = datetime.utcnow()
        agreement.valid_until = None
        agreement.metadata = {}
        agreement.status = "revoked"
        agreement.proof_id = "test-proof"
        agreement.timestamp_proof = "test-timestamp"

        tx_hash = ethereum_client.update_agreement(agreement)
        assert isinstance(tx_hash, str)
        assert tx_hash == "0x7478686173680000000000000000000000000000000000000000000000000000"

        