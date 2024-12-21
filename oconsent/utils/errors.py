# oconsent/utils/errors.py

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
    """Base class for storage-related errors."""
    pass

class StorageConnectionError(StorageError):
    """Raised when connection to storage service fails."""
    pass

class StorageTimeoutError(StorageError):
    """Raised when storage operation times out."""
    pass

class StorageQuotaError(StorageError):
    """Raised when storage quota is exceeded."""
    pass

class IPFSError(StorageError):
    """Base class for IPFS-specific errors."""
    pass

class IPFSConnectionError(IPFSError):
    """Raised when IPFS node connection fails."""
    pass

class IPFSPinningError(IPFSError):
    """Raised when IPFS pinning operation fails."""
    pass

class IPFSTimeoutError(IPFSError):
    """Raised when IPFS operation times out."""
    pass

class AuthorizationError(OConsentError):
    """Raised for authorization failures."""
    pass
