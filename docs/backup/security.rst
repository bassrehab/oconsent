Security Guide
============

Best Practices
------------

Private Key Management
~~~~~~~~~~~~~~~~~~

Never hardcode private keys or sensitive data:

.. code-block:: python

    # BAD
    private_key = "0x123..."  # Never do this!

    # GOOD
    from oconsent.utils.config import load_config
    config = load_config()
    private_key = config.get('ethereum.private_key')

Access Control
~~~~~~~~~~~

Always verify permissions:

.. code-block:: python

    # Verify processor authorization
    if not consent_manager.is_authorized_processor(processor_id):
        raise UnauthorizedError("Not an authorized processor")

    # Check purpose authorization
    if not consent_manager.can_process_purpose(agreement_id, purpose_id):
        raise UnauthorizedError("Not authorized for this purpose")

Data Privacy
~~~~~~~~~~

Minimize on-chain data:

.. code-block:: python

    # Store only hashes on-chain
    metadata_hash = consent_manager.hash_metadata(metadata)
    agreement = consent_manager.create_agreement(
        metadata_hash=metadata_hash,
        # ... other parameters
    )

    # Store actual data off-chain
    storage.store(metadata, reference=metadata_hash)