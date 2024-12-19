# tests/unit/test_consent.py

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from oconsent.core.consent import ConsentManager, ConsentPurpose, ConsentAgreement
from oconsent.utils.errors import ValidationError, ConsentError

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
        id="purpose-1",
        name="Analytics",
        description="Data analysis",
        retention_period=2592000,  # 30 days
        created_at=current_time
    )

@pytest.fixture
def sample_agreement_data(sample_purpose):
    return {
        "subject_id": "user-123",
        "processor_id": "processor-456",
        "purposes": [sample_purpose],
        "valid_from": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=365),
        "metadata": {"version": "1.0"}
    }

class TestConsentManager:
    def test_create_agreement_success(self, consent_manager, sample_agreement_data):
        """Test successful agreement creation"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        
        assert agreement.subject_id == sample_agreement_data["subject_id"]
        assert agreement.processor_id == sample_agreement_data["processor_id"]
        assert len(agreement.purposes) == 1
        assert agreement.status == "active"
        assert agreement.proof_id == "proof123"
        assert agreement.timestamp_proof == "timestamp123"

    def test_create_agreement_invalid_dates(self, consent_manager, sample_agreement_data):
        """Test agreement creation with invalid dates"""
        sample_agreement_data["valid_until"] = sample_agreement_data["valid_from"] - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            consent_manager.create_agreement(**sample_agreement_data)
        assert "valid_from must be before valid_until" in str(exc_info.value)

    def test_verify_consent_valid(self, consent_manager, mock_ethereum_client, sample_agreement_data):
        """Test consent verification for valid agreement"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        mock_ethereum_client.get_agreement.return_value = agreement

        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="purpose-1",
            processor_id="processor-456"
        )
        assert is_valid is True

    def test_verify_consent_expired(self, consent_manager, mock_ethereum_client, sample_agreement_data):
        """Test consent verification for expired agreement"""
        # Set both valid_from and valid_until in the past
        past_time = datetime.utcnow() - timedelta(days=2)  # 2 days ago
        expired_time = past_time + timedelta(days=1)       # 1 day ago
        
        sample_agreement_data["valid_from"] = past_time
        sample_agreement_data["valid_until"] = expired_time
        
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        mock_ethereum_client.get_agreement.return_value = agreement

        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="purpose-1",
            processor_id="processor-456"
        )
        assert is_valid is False

    def test_revoke_agreement(self, consent_manager, mock_ethereum_client, sample_agreement_data):
        """Test agreement revocation"""
        agreement = consent_manager.create_agreement(**sample_agreement_data)
        mock_ethereum_client.get_agreement.return_value = agreement

        revoked_agreement = consent_manager.revoke_agreement(agreement.id)
        assert revoked_agreement.status == "revoked"

        mock_ethereum_client.get_agreement.return_value = revoked_agreement
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="purpose-1",
            processor_id="processor-456"
        )
        assert is_valid is False
