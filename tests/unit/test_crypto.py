# tests/unit/test_crypto.py

import pytest
import json
from datetime import datetime
from unittest.mock import Mock
from oconsent.crypto.zk_proofs import ProofGenerator
from oconsent.utils.errors import ValidationError

@pytest.fixture
def proof_generator():
    return ProofGenerator()

@pytest.fixture
def mock_agreement():
    agreement = Mock()
    agreement.id = "test-id"
    agreement.subject_id = "test-subject"
    agreement.processor_id = "test-processor"
    agreement.valid_from = datetime.now()
    agreement.proof_id = None
    return agreement

class TestProofGenerator:
    def test_generate_proof(self, proof_generator, mock_agreement):
        """Test proof generation"""
        proof = proof_generator.generate_consent_proof(mock_agreement)
        assert proof is not None
        assert isinstance(proof, str)

    def test_verify_valid_proof(self, proof_generator, mock_agreement):
        """Test verification of valid proof"""
        proof = proof_generator.generate_consent_proof(mock_agreement)
        mock_agreement.proof_id = proof
        
        is_valid = proof_generator.verify_consent_proof(mock_agreement)
        assert is_valid is True

    def test_verify_invalid_proof(self, proof_generator, mock_agreement):
        """Test verification of invalid proof"""
        mock_agreement.proof_id = "invalid-proof"
        
        is_valid = proof_generator.verify_consent_proof(mock_agreement)
        assert is_valid is False

    def test_verify_missing_proof(self, proof_generator, mock_agreement):
        """Test verification with missing proof"""
        mock_agreement.proof_id = None
        
        is_valid = proof_generator.verify_consent_proof(mock_agreement)
        assert is_valid is False
        