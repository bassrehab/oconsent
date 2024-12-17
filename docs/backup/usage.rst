Usage Guide
==========

Basic Usage
----------

Creating a Consent Agreement
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from oconsent import ConsentManager
    from oconsent.blockchain.ethereum import EthereumClient
    
    # Initialize components
    ethereum_client = EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...',
        private_key='0x...'
    )
    
    consent_manager = ConsentManager(
        blockchain_client=ethereum_client
    )
    
    # Create an agreement
    agreement = consent_manager.create_agreement(
        subject_id="user123",
        processor_id="company456",
        purposes=[{
            "id": "data-analytics",
            "name": "Data Analytics",
            "description": "Process data for analytics",
            "retention_period": 30 * 24 * 60 * 60  # 30 days
        }],
        valid_from=datetime.now(),
        valid_until=datetime.now() + timedelta(days=365)
    )

Verifying Consent
~~~~~~~~~~~~~~~

.. code-block:: python

    # Verify consent for a specific purpose
    is_valid = consent_manager.verify_consent(
        agreement_id="agreement123",
        purpose_id="data-analytics",
        processor_id="company456"
    )
    
    if is_valid:
        print("Consent is valid")
    else:
        print("Consent is not valid")

Working with Multiple Purposes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Add new purpose to existing agreement
    consent_manager.add_purpose(
        agreement_id="agreement123",
        purpose={
            "id": "email-marketing",
            "name": "Email Marketing",
            "description": "Send marketing emails",
            "retention_period": 90 * 24 * 60 * 60  # 90 days
        }
    )