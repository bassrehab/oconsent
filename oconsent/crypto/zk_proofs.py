from typing import Dict, Optional
from hashlib import sha256
import json
from dataclasses import asdict

class ProofGenerator:
    """Handles zero-knowledge proof generation and verification."""
    
    def __init__(self, snark_params_path: Optional[str] = None):
        self.snark_params_path = snark_params_path
        
    def generate_consent_proof(self, agreement: 'ConsentAgreement') -> str:
        """Generates a zero-knowledge proof for a consent agreement.
        
        For testing/demo purposes, this creates a simple hash-based proof.
        In production, this would use actual ZK-SNARK proofs.
        """
        proof_data = {
            'agreement_id': agreement.id,
            'subject_id': agreement.subject_id,
            'processor_id': agreement.processor_id,
            'timestamp': str(agreement.valid_from.timestamp()),
            'metadata': getattr(agreement, 'metadata', {}),
            'purposes_hash': self._hash_purposes(getattr(agreement, 'purposes', None)),
            'status': getattr(agreement, 'status', 'ACTIVE'),
            'valid_until': str(agreement.valid_until.timestamp()) if getattr(agreement, 'valid_until', None) else '0'
        }
            
        # Create a simple hash-based proof for testing
        try:
            proof = sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
            return proof
        except (AttributeError, TypeError):
            # Handle case where agreement attributes are not properly accessible
            return sha256(b'').hexdigest()
        
    
    def verify_consent_proof(self, agreement: 'ConsentAgreement') -> bool:
        """Verifies a zero-knowledge proof for a consent agreement.
        
        For testing/demo purposes, this recreates and verifies the hash.
        In production, this would verify actual ZK-SNARK proofs.
        """
        if not agreement.proof_id:
            return False
            
        try:
            current_proof = self.generate_consent_proof(agreement)
            return current_proof == agreement.proof_id
        except Exception:
            return False
    
    
    def _create_witness(self, agreement: 'ConsentAgreement') -> Dict:
        """Creates a witness for the ZK-SNARK proof."""
        if not agreement:
            return {'private': {}, 'public': {}}

        # Create private inputs (not revealed in the proof)
        try:
            private_inputs = {
                'subject_id': agreement.subject_id,
                'metadata': getattr(agreement, 'metadata', {}),
                'purposes_hash': self._hash_purposes(getattr(agreement, 'purposes', None))
            }
            
            # Create public inputs (revealed in the proof)
            public_inputs = {
                'processor_id': agreement.processor_id,
                'valid_from': int(agreement.valid_from.timestamp()),
                'valid_until': int(agreement.valid_until.timestamp()) if getattr(agreement, 'valid_until', None) else 0,
                'status': getattr(agreement, 'status', 'ACTIVE')
            }
            
            return {
                'private': private_inputs,
                'public': public_inputs
            }
        except (AttributeError, TypeError):
            return {'private': {}, 'public': {}}


    def _create_public_inputs(self, agreement: 'ConsentAgreement') -> Dict:
        """Creates public inputs for proof verification."""
        try:
            return {
                'processor_id': agreement.processor_id,
                'valid_from': int(agreement.valid_from.timestamp()),
                'valid_until': int(agreement.valid_until.timestamp()) if getattr(agreement, 'valid_until', None) else 0,
                'status': getattr(agreement, 'status', 'ACTIVE')
            }
        except (AttributeError, TypeError):
            return {}
    
    def _hash_purposes(self, purposes: list) -> str:
        """Creates a hash of the consent purposes."""
        if purposes is None:
            return sha256(b'').hexdigest()
        
        try:
            if isinstance(purposes, list):
                purposes_data = [
                    p if isinstance(p, dict) else 
                    asdict(p) if hasattr(p, '__dict__') else 
                    p.__dict__ if hasattr(p, '__dict__') else {}
                    for p in purposes
                ]
            else:
                purposes_data = []
                
            purposes_str = json.dumps(purposes_data, sort_keys=True)
            return sha256(purposes_str.encode()).hexdigest()
        except (TypeError, AttributeError):
            return sha256(b'').hexdigest()
        