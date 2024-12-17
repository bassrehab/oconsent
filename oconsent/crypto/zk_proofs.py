# oconsent/crypto/zk_proofs.py

from typing import Dict, Optional
import json
from dataclasses import asdict
from hashlib import sha256
import zk_snark_client  # This would be a hypothetical ZK-SNARK library

class ProofGenerator:
    """Handles zero-knowledge proof generation and verification."""
    
    def __init__(self, snark_params_path: str):
        self.snark_client = zk_snark_client.Client(snark_params_path)
        
    def generate_consent_proof(self, agreement: 'ConsentAgreement') -> str:
        """Generates a zero-knowledge proof for a consent agreement."""
        # Create witness for the proof
        witness = self._create_witness(agreement)
        
        # Generate the proof
        proof = self.snark_client.generate_proof(
            circuit="consent_validity",
            witness=witness
        )
        
        return json.dumps(proof)
    
    def verify_consent_proof(self, agreement: 'ConsentAgreement') -> bool:
        """Verifies a zero-knowledge proof for a consent agreement."""
        if not agreement.proof_id:
            return False
            
        try:
            proof = json.loads(agreement.proof_id)
            public_inputs = self._create_public_inputs(agreement)
            
            return self.snark_client.verify_proof(
                circuit="consent_validity",
                proof=proof,
                public_inputs=public_inputs
            )
        except Exception:
            return False
    
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
        