# tests/test_consent.py

import pytest
from datetime import datetime, timedelta
from oconsent.core.consent import ConsentManager, ConsentPurpose
from oconsent.blockchain.ethereum import EthereumClient

@pytest.fixture
def ethereum_client():
    return EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...',
        private_key='0x...'
    )

@pytest.fixture
def consent_manager(ethereum_client):
    return ConsentManager(blockchain_client=ethereum_client)

def test_create_agreement(consent_manager):
    # Prepare test data
    current_time = datetime.utcnow()
    purpose = ConsentPurpose(
        id="test-purpose",
        name="Test Purpose",
        description="Test Description",
        retention_period=2592000,  # 30 days
        created_at=current_time
    )

    # Create agreement
    agreement = consent_manager.create_agreement(
        subject_id="test-subject",
        processor_id="test-processor",
        purposes=[purpose],
        valid_from=current_time,
        valid_until=current_time + timedelta(days=365)
    )

    # Assertions
    assert agreement.id is not None
    assert agreement.subject_id == "test-subject"
    assert agreement.processor_id == "test-processor"
    assert len(agreement.purposes) == 1
    assert agreement.purposes[0].id == "test-purpose"
    assert agreement.status == "active"

def test_verify_consent(consent_manager):
    # Create an agreement first
    current_time = datetime.utcnow()
    purpose = ConsentPurpose(
        id="test-purpose",
        name="Test Purpose",
        description="Test Description",
        retention_period=2592000,
        created_at=current_time
    )

    agreement = consent_manager.create_agreement(
        subject_id="test-subject",
        processor_id="test-processor",
        purposes=[purpose],
        valid_from=current_time,
        valid_until=current_time + timedelta(days=365)
    )

    # Verify consent
    is_valid = consent_manager.verify_consent(
        agreement_id=agreement.id,
        purpose_id="test-purpose",
        processor_id="test-processor"
    )

    assert is_valid is True

def test_revoke_agreement(consent_manager):
    # Create an agreement
    current_time = datetime.utcnow()
    purpose = ConsentPurpose(
        id="test-purpose",
        name="Test Purpose",
        description="Test Description",
        retention_period=2592000,
        created_at=current_time
    )

    agreement = consent_manager.create_agreement(
        subject_id="test-subject",
        processor_id="test-processor",
        purposes=[purpose],
        valid_from=current_time,
        valid_until=current_time + timedelta(days=365)
    )

    # Revoke agreement
    revoked_agreement = consent_manager.revoke_agreement(agreement.id)
    assert revoked_agreement.status == "revoked"

    # Verify consent is no longer valid
    is_valid = consent_manager.verify_consent(
        agreement_id=agreement.id,
        purpose_id="test-purpose",
        processor_id="test-processor"
    )
    assert is_valid is False