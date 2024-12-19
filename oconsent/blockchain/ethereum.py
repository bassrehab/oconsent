from eth_typing import Address
from web3 import Web3
from typing import Dict, List, Optional
import json
from ..utils.errors import BlockchainError  


class EthereumClient:
    """Handles interactions with Ethereum blockchain."""
    
    def __init__(
        self,
        provider_url: str,
        contract_address: str,
        private_key: Optional[str] = None,
        contract_abi: Optional[Dict] = None
    ):
        try:
            # Initialize Web3
            self.web3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Convert contract address
            if not isinstance(contract_address, str):
                raise BlockchainError("Contract address must be a string")
            self.contract_address = Address(bytes.fromhex(contract_address.replace('0x', '')))
            self.private_key = private_key

            # Load contract ABI
            if not contract_abi:
                raise BlockchainError("Contract ABI is required")
            self.contract_abi = contract_abi['abi']

            # Initialize contract
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
        except Exception as e:
            raise BlockchainError(f"Failed to initialize Ethereum client: {str(e)}")


    def store_agreement(self, agreement: 'ConsentAgreement') -> str:
        """Stores a consent agreement on the blockchain."""
        # Prepare transaction data
        agreement_data = {
            'id': agreement.id,
            'subject_id': agreement.subject_id,
            'processor_id': agreement.processor_id,
            'purposes': [vars(p) for p in agreement.purposes],
            'valid_from': int(agreement.valid_from.timestamp()),
            'valid_until': int(agreement.valid_until.timestamp()) if agreement.valid_until else 0,
            'metadata': agreement.metadata,
            'status': agreement.status,
            'proof_id': agreement.proof_id,
            'timestamp_proof': agreement.timestamp_proof
        }
        
        # Build transaction
        tx = self.contract.functions.storeAgreement(
            agreement.id,
            agreement_data
        ).build_transaction({
            'from': self.web3.eth.account.from_key(self.private_key).address,
            'nonce': self.web3.eth.get_transaction_count(
                self.web3.eth.account.from_key(self.private_key).address
            )
        })
        
        # Sign and send transaction
        signed_tx = self.web3.eth.account.sign_transaction(
            tx,
            self.private_key
        )
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        return receipt.transactionHash.hex()
    
    def get_agreement(self, agreement_id: str) -> Optional['ConsentAgreement']:
        """Retrieves a consent agreement from the blockchain."""
        try:
            agreement_data = self.contract.functions.getAgreement(agreement_id).call()
            if not agreement_data:
                return None
                
            # Convert blockchain data back to ConsentAgreement object
            return self._deserialize_agreement(agreement_data)
        except Exception as e:
            raise BlockchainError(f"Failed to retrieve consent agreement: {str(e)}")
    
    def update_agreement(self, agreement: 'ConsentAgreement') -> str:
        """Updates an existing consent agreement on the blockchain."""
        return self.store_agreement(agreement)
    
    def query_agreements(
        self,
        subject_id: Optional[str] = None,
        processor_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List['ConsentAgreement']:
        """Queries consent agreements based on filters."""
        # Call contract method to get filtered agreements
        agreement_ids = self.contract.functions.queryAgreements(
            subject_id or '',
            processor_id or '',
            status or ''
        ).call()
        
        # Fetch full agreement data for each ID
        agreements = []
        for agreement_id in agreement_ids:
            agreement = self.get_agreement(agreement_id)
            if agreement:
                agreements.append(agreement)
                
        return agreements
    
    def _deserialize_agreement(self, data: Dict) -> 'ConsentAgreement':
        """Converts blockchain data back to ConsentAgreement object."""
        from oconsent.core.consent import ConsentAgreement, ConsentPurpose
        from datetime import datetime
        
        purposes = [
            ConsentPurpose(
                id=p['id'],
                name=p['name'],
                description=p['description'],
                retention_period=p['retention_period'],
                created_at=datetime.fromtimestamp(p['created_at'])
            )
            for p in data['purposes']
        ]
        
        return ConsentAgreement(
            id=data['id'],
            subject_id=data['subject_id'],
            processor_id=data['processor_id'],
            purposes=purposes,
            valid_from=datetime.fromtimestamp(data['valid_from']),
            valid_until=datetime.fromtimestamp(data['valid_until']) if data['valid_until'] else None,
            metadata=data['metadata'],
            status=data['status'],
            proof_id=data['proof_id'],
            timestamp_proof=data['timestamp_proof']
        )
    