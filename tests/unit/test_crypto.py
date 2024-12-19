import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock
from oconsent.crypto.zk_proofs import ProofGenerator
from oconsent.utils.errors import ValidationError


@pytest.fixture
def proof_generator():
    """Create a ProofGenerator instance"""
    return ProofGenerator()

@pytest.fixture
def mock_agreement():
    """Create a basic mock agreement"""
    agreement = Mock()
    agreement.id = "test-id"
    agreement.subject_id = "test-subject"
    agreement.processor_id = "test-processor"
    agreement.valid_from = datetime.now()
    agreement.valid_until = None
    agreement.proof_id = None
    agreement.status = "ACTIVE"
    return agreement

@pytest.fixture
def mock_agreement_with_data():
    """Create a mock agreement with complete data"""
    agreement = Mock()
    agreement.id = "test-id"
    agreement.subject_id = "test-subject"
    agreement.processor_id = "test-processor"
    agreement.valid_from = datetime.now()
    agreement.valid_until = datetime.now() + timedelta(days=30)
    agreement.purposes = [
        {
            "purpose": "marketing",
            "data": ["email", "phone"],
            "retention": "30_days"
        },
        {
            "purpose": "analytics",
            "data": ["usage_stats"],
            "retention": "90_days"
        }
    ]
    agreement.metadata = {
        "version": "1.0",
        "region": "EU",
        "data_category": "personal",
        "creation_time": datetime.now().isoformat()
    }
    agreement.status = "ACTIVE"
    agreement.proof_id = None
    return agreement

class TestProofGenerator:
    def test_generate_proof(self, proof_generator, mock_agreement):
        """Test basic proof generation"""
        proof = proof_generator.generate_consent_proof(mock_agreement)
        assert proof is not None
        assert isinstance(proof, str)
        assert len(proof) == 64  # SHA256 hash length in hex

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

    def test_create_witness(self, proof_generator, mock_agreement_with_data):
        """Test witness creation for ZK proofs"""
        witness = proof_generator._create_witness(mock_agreement_with_data)
        
        # Check structure
        assert 'private' in witness
        assert 'public' in witness
        
        # Check private inputs
        assert witness['private']['subject_id'] == mock_agreement_with_data.subject_id
        assert witness['private']['metadata'] == mock_agreement_with_data.metadata
        assert 'purposes_hash' in witness['private']
        
        # Check public inputs
        assert witness['public']['processor_id'] == mock_agreement_with_data.processor_id
        assert witness['public']['status'] == mock_agreement_with_data.status
        assert isinstance(witness['public']['valid_from'], int)
        
        if mock_agreement_with_data.valid_until:
            assert isinstance(witness['public']['valid_until'], int)

    def test_create_public_inputs(self, proof_generator, mock_agreement_with_data):
        """Test public inputs creation"""
        public_inputs = proof_generator._create_public_inputs(mock_agreement_with_data)
        
        # Check required fields
        assert 'processor_id' in public_inputs
        assert 'valid_from' in public_inputs
        assert 'status' in public_inputs
        
        # Check values
        assert public_inputs['processor_id'] == mock_agreement_with_data.processor_id
        assert public_inputs['status'] == mock_agreement_with_data.status
        assert isinstance(public_inputs['valid_from'], int)
        assert isinstance(public_inputs.get('valid_until', 0), int)

    def test_hash_purposes(self, proof_generator, mock_agreement_with_data):
        """Test purposes hashing"""
        purposes_hash = proof_generator._hash_purposes(mock_agreement_with_data.purposes)
        
        # Check hash properties
        assert isinstance(purposes_hash, str)
        assert len(purposes_hash) == 64  # SHA256 hash length in hex
        
        # Test deterministic hash
        purposes_hash2 = proof_generator._hash_purposes(mock_agreement_with_data.purposes)
        assert purposes_hash == purposes_hash2

    def test_proof_with_complex_agreement(self, proof_generator, mock_agreement_with_data):
        """Test proof generation with complex agreement data"""
        # Generate and verify initial proof
        proof = proof_generator.generate_consent_proof(mock_agreement_with_data)
        mock_agreement_with_data.proof_id = proof
        assert proof_generator.verify_consent_proof(mock_agreement_with_data) is True
        
        # Modify agreement and verify proof fails
        mock_agreement_with_data.purposes.append({
            "purpose": "new_purpose",
            "data": ["new_data"],
            "retention": "60_days"
        })
        assert proof_generator.verify_consent_proof(mock_agreement_with_data) is False

    def test_empty_purposes(self, proof_generator, mock_agreement_with_data):
        """Test handling of empty purposes list"""
        mock_agreement_with_data.purposes = []
        purposes_hash = proof_generator._hash_purposes(mock_agreement_with_data.purposes)
        assert purposes_hash is not None
        assert isinstance(purposes_hash, str)
        assert len(purposes_hash) == 64

    def test_none_purposes(self, proof_generator, mock_agreement_with_data):
        """Test handling of None purposes"""
        mock_agreement_with_data.purposes = None
        purposes_hash = proof_generator._hash_purposes(mock_agreement_with_data.purposes)
        assert purposes_hash is not None
        assert isinstance(purposes_hash, str)
        assert len(purposes_hash) == 64

    def test_deterministic_proof_generation(self, proof_generator, mock_agreement_with_data):
        """Test that proof generation is deterministic"""
        proof1 = proof_generator.generate_consent_proof(mock_agreement_with_data)
        proof2 = proof_generator.generate_consent_proof(mock_agreement_with_data)
        assert proof1 == proof2

    def test_agreement_modification_detection(self, proof_generator, mock_agreement_with_data):
        """Test that any agreement modification invalidates the proof"""
        # Generate initial proof
        proof = proof_generator.generate_consent_proof(mock_agreement_with_data)
        mock_agreement_with_data.proof_id = proof
        
        assert proof_generator.verify_consent_proof(mock_agreement_with_data) is True
        
        # Test various modifications
        modifications = [
            ('subject_id', 'new-subject'),
            ('processor_id', 'new-processor'),
            ('status', 'INACTIVE'),
            ('valid_from', datetime.now() + timedelta(days=1))
        ]
        
        for field, new_value in modifications:
            original_value = getattr(mock_agreement_with_data, field)
            setattr(mock_agreement_with_data, field, new_value)
            
            assert proof_generator.verify_consent_proof(mock_agreement_with_data) is False
            
            # Restore original value
            setattr(mock_agreement_with_data, field, original_value)
            assert proof_generator.verify_consent_proof(mock_agreement_with_data) is True

    def test_metadata_changes(self, proof_generator, mock_agreement_with_data):
        """Test that metadata changes affect the proof"""
        # Generate initial proof
        proof = proof_generator.generate_consent_proof(mock_agreement_with_data)
        mock_agreement_with_data.proof_id = proof
        
        # Modify metadata
        original_metadata = mock_agreement_with_data.metadata.copy()
        mock_agreement_with_data.metadata['new_field'] = 'new_value'
        
        assert proof_generator.verify_consent_proof(mock_agreement_with_data) is False
        
        # Restore original metadata
        mock_agreement_with_data.metadata = original_metadata
        assert proof_generator.verify_consent_proof(mock_agreement_with_data) is True

    def test_timestamp_handling(self, proof_generator, mock_agreement_with_data):
        """Test proper handling of timestamps in proof generation"""
        # Test with valid_until = None
        mock_agreement_with_data.valid_until = None
        proof = proof_generator.generate_consent_proof(mock_agreement_with_data)
        assert proof is not None
        
        # Test with valid_until in the future
        future_time = datetime.now() + timedelta(days=30)
        mock_agreement_with_data.valid_until = future_time
        proof = proof_generator.generate_consent_proof(mock_agreement_with_data)
        assert proof is not None
        
        # Verify timestamps are properly included in witness
        witness = proof_generator._create_witness(mock_agreement_with_data)
        assert isinstance(witness['public']['valid_from'], int)
        assert isinstance(witness['public']['valid_until'], int)
