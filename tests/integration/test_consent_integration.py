# tests/integration/test_consent_integration.py

import pytest
from datetime import datetime, timedelta
from oconsent.core.consent import ConsentManager, ConsentPurpose
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.crypto.zk_proofs import ProofGenerator
from oconsent.core.timestamp import TimestampService

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
    """Real proof generator for integration tests"""
    return ProofGenerator('path/to/snark/params')

@pytest.fixture
def timestamp_service():
    """Real timestamp service for integration tests"""
    return TimestampService()

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
        assert agreement.timestamp_proof is not None

        # Verify consent is valid
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id=test_agreement_data["purposes"][0]["id"],
            processor_id=test_agreement_data["processor_id"]
        )
        assert is_valid is True

        # Revoke agreement
        revoked = consent_manager.revoke_agreement(agreement.id)
        assert revoked.status == "revoked"

        # Verify consent is now invalid
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id=test_agreement_data["purposes"][0]["id"],
            processor_id=test_agreement_data["processor_id"]
        )
        assert is_valid is False