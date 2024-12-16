# oconsent/core/consent.py

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import uuid

@dataclass
class ConsentPurpose:
    """Represents a specific purpose for data processing."""
    id: str
    name: str
    description: str
    retention_period: int  # in seconds
    created_at: datetime

@dataclass
class ConsentAgreement:
    """Represents a consent agreement between a data subject and processor."""
    id: str
    subject_id: str
    processor_id: str
    purposes: List[ConsentPurpose]
    valid_from: datetime
    valid_until: Optional[datetime]
    metadata: Dict
    status: str  # active, revoked, expired
    proof_id: Optional[str]  # Reference to zero-knowledge proof
    timestamp_proof: Optional[str]  # Reference to timestamp proof

class ConsentManager:
    """Manages consent agreements and their lifecycle."""
    
    def __init__(self, blockchain_client, proof_generator, timestamp_service):
        self.blockchain_client = blockchain_client
        self.proof_generator = proof_generator
        self.timestamp_service = timestamp_service
        
    def create_agreement(
        self,
        subject_id: str,
        processor_id: str,
        purposes: List[ConsentPurpose],
        valid_from: datetime,
        valid_until: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> ConsentAgreement:
        """Creates a new consent agreement."""
        agreement = ConsentAgreement(
            id=str(uuid.uuid4()),
            subject_id=subject_id,
            processor_id=processor_id,
            purposes=purposes,
            valid_from=valid_from,
            valid_until=valid_until,
            metadata=metadata or {},
            status="active",
            proof_id=None,
            timestamp_proof=None
        )
        
        # Generate zero-knowledge proof
        agreement.proof_id = self.proof_generator.generate_consent_proof(agreement)
        
        # Get timestamp proof
        agreement.timestamp_proof = self.timestamp_service.timestamp(agreement)
        
        # Store on blockchain
        self.blockchain_client.store_agreement(agreement)
        
        return agreement
    
    def revoke_agreement(self, agreement_id: str) -> ConsentAgreement:
        """Revokes an existing consent agreement."""
        agreement = self.blockchain_client.get_agreement(agreement_id)
        if not agreement:
            raise ValueError(f"Agreement {agreement_id} not found")
            
        agreement.status = "revoked"
        agreement.timestamp_proof = self.timestamp_service.timestamp(agreement)
        
        # Store revocation on blockchain
        self.blockchain_client.update_agreement(agreement)
        
        return agreement
    
    def verify_consent(
        self,
        agreement_id: str,
        purpose_id: str,
        processor_id: str
    ) -> bool:
        """Verifies if consent exists and is valid for a specific purpose."""
        agreement = self.blockchain_client.get_agreement(agreement_id)
        if not agreement:
            return False
            
        if agreement.status != "active":
            return False
            
        if agreement.processor_id != processor_id:
            return False
            
        # Check if purpose exists in agreement
        if not any(p.id == purpose_id for p in agreement.purposes):
            return False
            
        # Check temporal validity
        now = datetime.utcnow()
        if agreement.valid_from > now:
            return False
            
        if agreement.valid_until and agreement.valid_until < now:
            return False
            
        # Verify proofs
        if not self.proof_generator.verify_consent_proof(agreement):
            return False
            
        if not self.timestamp_service.verify_timestamp(agreement):
            return False
            
        return True
    
    def list_agreements(
        self,
        subject_id: Optional[str] = None,
        processor_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ConsentAgreement]:
        """Lists consent agreements based on optional filters."""
        return self.blockchain_client.query_agreements(
            subject_id=subject_id,
            processor_id=processor_id,
            status=status
        )
    