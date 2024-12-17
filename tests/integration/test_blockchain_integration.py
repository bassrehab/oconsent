# tests/integration/test_blockchain_integration.py

import pytest
from datetime import datetime, timedelta
from oconsent.blockchain.ethereum import EthereumClient
from oconsent.core.consent import ConsentManager

@pytest.mark.integration
class TestBlockchainIntegration:
    @pytest.fixture(scope="class")
    def ethereum_client(self):
        # Use local hardhat node for testing
        return EthereumClient(
            provider_url="http://localhost:8545",
            contract_address="<deployed_contract_address>",
            private_key="<test_private_key>"
        )

    @pytest.fixture(scope="class")
    def consent_manager(self, ethereum_client):
        return ConsentManager(blockchain_client=ethereum_client)

    def test_end_to_end_consent_flow(self, consent_manager):
        """Test complete consent lifecycle with blockchain integration"""
        # Create agreement
        agreement = consent_manager.create_agreement(
            subject_id="test-subject",
            processor_id="test-processor",
            purposes=[{
                "id": "purpose-1",
                "name": "Test Purpose",
                "description": "Integration test purpose",
                "retention_period": 2592000,
                "created_at": datetime.utcnow()
            }],
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )

        # Verify created agreement
        assert agreement.id is not None
        
        # Verify consent
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="purpose-1",
            processor_id="test-processor"
        )
        assert is_valid is True

        # Revoke agreement
        revoked = consent_manager.revoke_agreement(agreement.id)
        assert revoked.status == "revoked"

        # Verify consent is invalid after revocation
        is_valid = consent_manager.verify_consent(
            agreement_id=agreement.id,
            purpose_id="purpose-1",
            processor_id="test-processor"
        )
        assert is_valid is False
        