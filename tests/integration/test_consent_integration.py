from typing import Dict
import pytest
from datetime import datetime, timedelta
import json
from oconsent.core.consent import ConsentManager, ConsentPurpose
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.crypto.zk_proofs import ProofGenerator
from oconsent.core.timestamp import TimestampService, TimestampProvider


class MockNISTProvider(TimestampProvider):
    """Mock NIST Beacon provider for testing."""
    
    def get_timestamp(self) -> Dict:
        current_time = int(datetime.utcnow().timestamp())
        return {
            'timestamp': current_time,
            'randomness': 'test_random_value',
            'signature': 'test_signature',
            'type': 'nist'
        }
    
    def verify_timestamp(self, timestamp_proof: Dict) -> bool:
        return (
            timestamp_proof.get('type') == 'nist' and
            isinstance(timestamp_proof.get('timestamp'), int) and
            timestamp_proof.get('signature') == 'test_signature'
        )

class MockBitcoinProvider(TimestampProvider):
    """Mock Bitcoin provider for testing."""
    
    def get_timestamp(self) -> Dict:
        current_time = int(datetime.utcnow().timestamp())
        return {
            'timestamp': current_time,
            'block_hash': 'test_block_hash',
            'block_number': 1000,
            'type': 'bitcoin'
        }
    
    def verify_timestamp(self, timestamp_proof: Dict) -> bool:
        return (
            timestamp_proof.get('type') == 'bitcoin' and
            isinstance(timestamp_proof.get('timestamp'), int) and
            timestamp_proof.get('block_hash') == 'test_block_hash'
        )

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def ethereum_client(test_config):
    """Real Ethereum client for integration tests"""
    return EthereumClient(
        provider_url=test_config['ethereum']['provider_url'],
        contract_address=test_config['ethereum']['contract_address'],
        private_key=test_config['ethereum']['private_key']
    )

@pytest.fixture
def proof_generator():
    """Proof generator for integration tests"""
    return ProofGenerator()  # No params needed for test version

@pytest.fixture
def timestamp_service():
    """Timestamp service with mock providers for integration tests"""
    providers = {
        'nist': MockNISTProvider(),
        'bitcoin': MockBitcoinProvider()
    }
    return TimestampService(providers=providers)


@pytest.fixture
def consent_manager(ethereum_client, proof_generator, timestamp_service):
    """Consent manager with real dependencies"""
    return ConsentManager(
        blockchain_client=ethereum_client,
        proof_generator=proof_generator,
        timestamp_service=timestamp_service
    )

@pytest.fixture
def test_agreement_data():
    current_time = datetime.utcnow()
    return {
        "subject_id": "integration-test-subject",
        "processor_id": "integration-test-processor",
        "purposes": [{
            "id": "integration-purpose",
            "name": "Integration Test Purpose",
            "description": "Testing with real blockchain",
            "retention_period": 2592000,
            "created_at": current_time
        }],
        "valid_from": current_time,
        "valid_until": current_time + timedelta(days=365),
        "metadata": {"test_type": "integration"}
    }

class TestConsentIntegration:
    """Integration tests for consent management"""

    def test_end_to_end_consent_flow(self, consent_manager, test_agreement_data):
        """Test complete consent lifecycle with real blockchain"""
        # Create agreement
        agreement = consent_manager.create_agreement(**test_agreement_data)
        
        # Verify creation
        assert agreement.id is not None
        assert agreement.subject_id == test_agreement_data["subject_id"]
        assert agreement.proof_id is not None
        
        # Verify timestamp format
        assert agreement.timestamp_proof is not None
        timestamp_proofs = json.loads(agreement.timestamp_proof)
        assert 'nist' in timestamp_proofs
        assert 'bitcoin' in timestamp_proofs
        
        # Verify consent is valid
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id=test_agreement_data["purposes"][0]["id"],
            processor_id=test_agreement_data["processor_id"]
        )
        assert is_valid is True

        # Verify timestamp validation
        assert consent_manager.timestamp_service.verify_timestamp(agreement) is True

        # Revoke agreement
        revoked = consent_manager.revoke_agreement(agreement.id)
        assert revoked.status == "revoked"
        assert revoked.timestamp_proof is not None

        # Verify consent is now invalid
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id=test_agreement_data["purposes"][0]["id"],
            processor_id=test_agreement_data["processor_id"]
        )
        assert is_valid is False

    def test_timestamp_providers(self, timestamp_service):
        """Test that both timestamp providers are working"""
        timestamp = timestamp_service.timestamp(None)  # None is fine for testing
        proofs = json.loads(timestamp)
        
        assert 'nist' in proofs
        assert 'bitcoin' in proofs
        assert isinstance(proofs['nist']['timestamp'], int)
        assert isinstance(proofs['bitcoin']['timestamp'], int)

    def test_timestamp_verification(self, timestamp_service):
        """Test timestamp verification with mock providers"""
        class MockAgreement:
            def __init__(self, timestamp_proof):
                self.timestamp_proof = timestamp_proof

        # Create agreement with valid timestamp proof
        timestamp = timestamp_service.timestamp(None)
        agreement = MockAgreement(timestamp)
        
        # Verify timestamp
        assert timestamp_service.verify_timestamp(agreement) is True

        # Test with invalid timestamp
        invalid_agreement = MockAgreement('{"invalid": "proof"}')
        assert timestamp_service.verify_timestamp(invalid_agreement) is False
        