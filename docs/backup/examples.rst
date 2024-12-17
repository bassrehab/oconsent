Examples
========

Basic Consent Management
---------------------

Complete example of consent lifecycle management:

.. code-block:: python

    from oconsent import ConsentManager, EthereumClient
    from datetime import datetime, timedelta

    # Setup
    ethereum_client = EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...',
        private_key='0x...'
    )
    
    consent_manager = ConsentManager(blockchain_client=ethereum_client)

    # Create agreement
    agreement = consent_manager.create_agreement(
        subject_id="user123",
        processor_id="company456",
        purposes=[{
            "id": "data-analytics",
            "name": "Data Analytics",
            "description": "Process data for analytics",
            "retention_period": 30 * 24 * 60 * 60
        }],
        valid_from=datetime.now(),
        valid_until=datetime.now() + timedelta(days=365),
        metadata={"category": "analytics", "version": "1.0"}
    )

    # Verify consent
    is_valid = consent_manager.verify_consent(
        agreement_id=agreement.id,
        purpose_id="data-analytics",
        processor_id="company456"
    )

    # Add new purpose
    consent_manager.add_purpose(
        agreement_id=agreement.id,
        purpose={
            "id": "email-marketing",
            "name": "Email Marketing",
            "description": "Send marketing emails",
            "retention_period": 90 * 24 * 60 * 60
        }
    )

    # Revoke consent
    consent_manager.revoke_agreement(agreement.id)

Advanced Use Cases
---------------

Multi-Party Consent Chain
~~~~~~~~~~~~~~~~~~~~~~~

Example of handling consent across multiple processors:

.. code-block:: python

    # Create primary agreement
    primary_agreement = consent_manager.create_agreement(
        subject_id="user123",
        processor_id="primary_processor",
        purposes=[{
            "id": "collect-data",
            "name": "Data Collection",
            "description": "Initial data collection",
            "retention_period": 30 * 24 * 60 * 60
        }],
        valid_from=datetime.now()
    )

    # Create secondary agreement
    secondary_agreement = consent_manager.create_agreement(
        subject_id="user123",
        processor_id="secondary_processor",
        purposes=[{
            "id": "process-data",
            "name": "Data Processing",
            "description": "Secondary processing",
            "retention_period": 15 * 24 * 60 * 60
        }],
        valid_from=datetime.now(),
        metadata={"primary_agreement": primary_agreement.id}
    )

Batch Operations
~~~~~~~~~~~~~

Example of batch consent verification:

.. code-block:: python

    # Verify multiple consents
    results = consent_manager.batch_verify_consents([
        {
            "agreement_id": "agreement1",
            "purpose_id": "purpose1",
            "processor_id": "processor1"
        },
        {
            "agreement_id": "agreement2",
            "purpose_id": "purpose2",
            "processor_id": "processor2"
        }
    ])

    for result in results:
        print(f"Agreement {result['agreement_id']}: {'Valid' if result['valid'] else 'Invalid'}")