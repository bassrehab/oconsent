from typing import Dict, Optional
from hashlib import sha256
import json

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
            'timestamp': str(agreement.valid_from.timestamp())
        }
        
        # Create a simple hash-based proof for testing
        proof = sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
        
        return proof
    
    def verify_consent_proof(self, agreement: 'ConsentAgreement') -> bool:
        """Verifies a zero-knowledge proof for a consent agreement.
        
        For testing/demo purposes, this recreates and verifies the hash.
        In production, this would verify actual ZK-SNARK proofs.
        """
        if not agreement.proof_id:
            return False
            
        # Recreate proof for verification
        proof_data = {
            'agreement_id': agreement.id,
            'subject_id': agreement.subject_id,
            'processor_id': agreement.processor_id,
            'timestamp': str(agreement.valid_from.timestamp())
        }
        
        verification_proof = sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
        
        return verification_proof == agreement.proof_id
    
    
    def _create_witness(self, agreement: 'ConsentAgreement') -> Dict:
        """Creates a witness for the ZK-SNARK proof."""
        agreement_dict = asdict(agreement)
        
        # Create private inputs (not revealed in the proof)
        private_inputs = {
            'subject_id': agreement.subject_id,
            'metadata': agreement.metadata,
            'purposes_hash': self._hash_purposes(agreement.purposes)
        }
        
        # Create public inputs (revealed in the proof)
        public_inputs = {
            'processor_id': agreement.processor_id,
            'valid_from': int(agreement.valid_from.timestamp()),
            'valid_until': int(agreement.valid_until.timestamp()) if agreement.valid_until else 0,
            'status': agreement.status
        }
        
        return {
            'private': private_inputs,
            'public': public_inputs
        }
    
    def _create_public_inputs(self, agreement: 'ConsentAgreement') -> Dict:
        """Creates public inputs for proof verification."""
        return {
            'processor_id': agreement.processor_id,
            'valid_from': int(agreement.valid_from.timestamp()),
            'valid_until': int(agreement.valid_until.timestamp()) if agreement.valid_until else 0,
            'status': agreement.status
        }
    
    def _hash_purposes(self, purposes: list) -> str:
        """Creates a hash of the consent purposes."""
        purposes_str = json.dumps(
            [asdict(p) for p in purposes],
            sort_keys=True
        )
        return sha256(purposes_str.encode()).hexdigest()

# oconsent/crypto/signatures.py

from typing import Optional
from eth_account.messages import encode_defunct
from web3 import Web3
import time

class SignatureManager:
    """Handles digital signatures for consent operations."""
    
    def __init__(self, web3: Web3):
        self.web3 = web3
    
    def sign_consent(
        self,
        agreement_id: str,
        private_key: str,
        timestamp: Optional[int] = None
    ) -> str:
        """Signs a consent agreement."""
        if timestamp is None:
            timestamp = int(time.time())
            
        # Create message hash
        message = f"{agreement_id}:{timestamp}"
        message_hash = encode_defunct(text=message)
        
        # Sign message
        signed = self.web3.eth.account.sign_message(
            message_hash,
            private_key=private_key
        )
        
        return signed.signature.hex()
    
    def verify_signature(
        self,
        agreement_id: str,
        signature: str,
        address: str,
        timestamp: int
    ) -> bool:
        """Verifies a consent signature."""
        try:
            # Recreate message hash
            message = f"{agreement_id}:{timestamp}"
            message_hash = encode_defunct(text=message)
            
            # Recover signer address
            recovered_address = self.web3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            
            return recovered_address.lower() == address.lower()
        except Exception:
            return False
        