import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from oconsent.core.consent import ConsentManager, ConsentPurpose
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.utils.errors import ValidationError

# Real client for integration tests
@pytest.fixture
def ethereum_client():
    return EthereumClient(
        provider_url='http://localhost:8545',
        # Use a valid hex address for testing
        contract_address='0x0000000000000000000000000000000000000000',
        private_key='0x0000000000000000000000000000000000000000000000000000000000000000'
    )

# Mock clients for unit tests
@pytest.fixture
def mock_ethereum_client():
    client = Mock()
    client.store_agreement.return_value = True
    client.get_agreement.return_value = None
    return client

@pytest.fixture
def mock_proof_generator():
    generator = Mock()
    generator.generate_consent_proof.return_value = "proof123"
    generator.verify_consent_proof.return_value = True
    return generator

@pytest.fixture
def mock_timestamp_service():
    service = Mock()
    service.timestamp.return_value = "timestamp123"
    service.verify_timestamp.return_value = True
    return service

@pytest.fixture
def consent_manager(mock_ethereum_client, mock_proof_generator, mock_timestamp_service):
    return ConsentManager(
        blockchain_client=mock_ethereum_client,
        proof_generator=mock_proof_generator,
        timestamp_service=mock_timestamp_service
    )

@pytest.fixture
def sample_purpose():
    current_time = datetime.utcnow()
    return ConsentPurpose(
        id="test-purpose",
        name="Test Purpose",
        description="Test Description",
        retention_period=2592000,  # 30 days
        created_at=current_time
    )

@pytest.fixture
def sample_agreement_data(sample_purpose):
    current_time = datetime.utcnow()
    return {
        "subject_id": "user-123",
        "processor_id": "processor-456",
        "purposes": [sample_purpose],
        "valid_from": current_time,
        "valid_until": current_time + timedelta(days=365),
        "metadata": {"version": "1.0"}
    }

class TestConsentManager:
    """Test suite for ConsentManager"""

    def test_create_agreement_success(self, consent_manager, sample_agreement_data):
        """Test successful agreement creation"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        assert agreement.id is not None
        assert agreement.subject_id == sample_agreement_data["subject_id"]
        assert agreement.processor_id == sample_agreement_data["processor_id"]
        assert len(agreement.purposes) == 1
        assert agreement.purposes[0].id == "test-purpose"
        assert agreement.status == "active"
        assert agreement.proof_id == "proof123"
        assert agreement.timestamp_proof == "timestamp123"

    def test_create_agreement_invalid_dates(self, consent_manager, sample_agreement_data):
        """Test agreement creation with invalid dates"""
        sample_agreement_data["valid_until"] = sample_agreement_data["valid_from"] - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            consent_manager.create_agreement(**sample_agreement_data)
        assert "valid_from must be before valid_until" in str(exc_info.value)

    def test_verify_consent_valid(self, consent_manager, sample_agreement_data):
        """Test consent verification for valid agreement"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="test-purpose",
            processor_id=sample_agreement_data["processor_id"]
        )
        
        assert is_valid is True

    def test_verify_consent_expired(self, consent_manager, sample_agreement_data):
        """Test consent verification for expired agreement"""
        # Create expired agreement
        sample_agreement_data["valid_until"] = datetime.utcnow() - timedelta(days=1)
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="test-purpose",
            processor_id=sample_agreement_data["processor_id"]
        )
        
        assert is_valid is False

    def test_revoke_agreement(self, consent_manager, sample_agreement_data):
        """Test agreement revocation"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        # Revoke agreement
        revoked_agreement = consent_manager.revoke_agreement(agreement.id)
        assert revoked_agreement.status == "revoked"

        # Verify consent is no longer valid
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="test-purpose",
            processor_id=sample_agreement_data["processor_id"]
        )
        assert is_valid is False

    def test_verify_consent_wrong_processor(self, consent_manager, sample_agreement_data):
        """Test consent verification with wrong processor"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="test-purpose",
            processor_id="wrong-processor"
        )
        
        assert is_valid is False

    def test_verify_consent_wrong_purpose(self, consent_manager, sample_agreement_data):
        """Test consent verification with wrong purpose"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="wrong-purpose",
            processor_id=sample_agreement_data["processor_id"]
        )
        
        assert is_valid is False
