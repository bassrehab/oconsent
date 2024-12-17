
from datetime import datetime
from typing import Dict, List, Optional
from .errors import ValidationError

def validate_purpose(purpose: Dict) -> None:
    """Validates a purpose dictionary."""
    required_fields = ['id', 'name', 'description', 'retention_period']
    
    for field in required_fields:
        if field not in purpose:
            raise ValidationError(f"Missing required field: {field}")
            
    if not isinstance(purpose['retention_period'], int):
        raise ValidationError("retention_period must be an integer")
        
    if purpose['retention_period'] <= 0:
        raise ValidationError("retention_period must be positive")

def validate_agreement_dates(valid_from: datetime, valid_until: Optional[datetime]) -> None:
    """Validates agreement dates."""
    if valid_until and valid_from >= valid_until:
        raise ValidationError("valid_from must be before valid_until")

def validate_processor_id(processor_id: str) -> None:
    """Validates processor ID format."""
    if not processor_id or not isinstance(processor_id, str):
        raise ValidationError("Invalid processor ID")
    