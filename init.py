"""OConsent - Open Consent Protocol Implementation."""

__version__ = "0.1.0"
__author__ = "Subhadip Mitra"
__email__ = "contact@subhadipmitra.com"

from .core.consent import ConsentManager
from .blockchain.ethereum import EthereumClient
from .crypto.zk_proofs import ProofGenerator
from .core.timestamp import TimestampService

__all__ = [
    "ConsentManager",
    "EthereumClient",
    "ProofGenerator",
    "TimestampService",
]