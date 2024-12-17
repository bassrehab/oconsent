API Reference
============

Core Components
-------------

ConsentManager
~~~~~~~~~~~~

.. autoclass:: oconsent.core.consent.ConsentManager
    :members:
    :undoc-members:
    :show-inheritance:

.. code-block:: python

    class ConsentManager:
        """Manages consent agreements and their lifecycle."""
        
        def create_agreement(
            self,
            subject_id: str,
            processor_id: str,
            purposes: List[Dict],
            valid_from: datetime,
            valid_until: Optional[datetime] = None,
            metadata: Optional[Dict] = None
        ) -> ConsentAgreement:
            """Creates a new consent agreement."""
            pass

        def verify_consent(
            self,
            agreement_id: str,
            purpose_id: str,
            processor_id: str
        ) -> bool:
            """Verifies if consent exists and is valid."""
            pass

Blockchain Components
------------------

EthereumClient
~~~~~~~~~~~~

.. autoclass:: oconsent.blockchain.ethereum.EthereumClient
    :members:
    :undoc-members:
    :show-inheritance:

Storage Components
---------------

IPFSStorageProvider
~~~~~~~~~~~~~~~~

.. autoclass:: oconsent.storage.providers.IPFSStorageProvider
    :members:
    :undoc-members:
    :show-inheritance: