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
        