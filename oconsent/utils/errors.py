class OConsentError(Exception):
    """Base exception for OConsent errors."""
    pass

class BlockchainError(OConsentError):
    """Raised when blockchain operations fail."""
    pass

class ValidationError(OConsentError):
    """Raised when data validation fails."""
    pass

class ConsentError(OConsentError):
    """Raised for consent-related errors."""
    pass

class StorageError(OConsentError):
    """Raised when storage operations fail."""
    pass

class AuthorizationError(OConsentError):
    """Raised for authorization failures."""
    pass
