"""OConsent - Open Consent Protocol Implementation."""

__version__ = "0.1.0"
__author__ = "Subhadip Mitra"
__email__ = "contact@subhadipmitra.com"

from .oconsent.core.consent import ConsentManager
from .oconsent.blockchain.ethereum import EthereumClient
from .oconsent.crypto.zk_proofs import ProofGenerator
from .oconsent.core.timestamp import TimestampService

__all__ = [
    "ConsentManager",
    "EthereumClient",
    "ProofGenerator",
    "TimestampService",
]