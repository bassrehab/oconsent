# docs/source/testing.rst

Testing Guide
============

OConsent has comprehensive test coverage including unit tests, integration tests, and blockchain tests. This guide covers all testing aspects.

Test Categories
-------------

Unit Tests
~~~~~~~~~

Run unit tests with:

.. code-block:: console

    $ pytest tests/unit/

Key unit test files:

- ``test_consent.py``: Tests core consent management
- ``test_crypto.py``: Tests cryptographic components
- ``test_blockchain.py``: Tests blockchain interactions
- ``test_ipfs.py``: Tests IPFS storage provider

Integration Tests
~~~~~~~~~~~~~~~

Run integration tests with:

.. code-block:: console

    $ pytest tests/integration/

Key integration test files:

- ``test_consent_integration.py``: End-to-end consent flows
- ``test_blockchain_integration.py``: Live blockchain interactions
- ``test_ipfs_integration.py``: IPFS storage integration

Test Setup
---------

1. Environment Setup
~~~~~~~~~~~~~~~~~~

Create a test environment file ``.env.test``:

.. code-block:: text

    # Ethereum Test Settings
    ETH_PROVIDER_URL=http://localhost:8545
    ETH_PRIVATE_KEY=your_test_private_key
    ETH_CONTRACT_ADDRESS=your_test_contract_address

    # IPFS Test Settings
    IPFS_NODE=/ip4/127.0.0.1/tcp/5001
    IPFS_GATEWAY=https://ipfs.io
    IPFS_PINNING_SERVICE=optional_pinning_service_url
    IPFS_PINNING_KEY=optional_pinning_service_key

2. Blockchain Setup
~~~~~~~~~~~~~~~~~

For blockchain tests:

.. code-block:: console

    # Start local Hardhat node
    $ cd contracts
    $ npx hardhat node

    # Deploy test contracts
    $ npx hardhat run scripts/deploy.js --network localhost

3. IPFS Setup
~~~~~~~~~~~~

For IPFS tests:

.. code-block:: console

    # Start IPFS daemon
    $ ipfs init  # If not already initialized
    $ ipfs daemon

Running Tests
-----------

Run all tests:

.. code-block:: console

    $ pytest

Run specific test categories:

.. code-block:: console

    # Run only unit tests
    $ pytest tests/unit/

    # Run only integration tests
    $ pytest tests/integration/

    # Run tests with coverage
    $ pytest --cov=oconsent

    # Run specific test file
    $ pytest tests/unit/test_crypto.py

Test Configuration
----------------

Configure test behavior using ``pytest.ini``:

.. code-block:: ini

    [pytest]
    markers =
        integration: mark test as integration test
        blockchain: mark test as requiring blockchain
        ipfs: mark test as requiring IPFS
    asyncio_mode = strict
    log_cli = true
    log_cli_level = INFO

Common Test Flags
---------------

Useful pytest flags:

- ``-v``: Verbose output
- ``-s``: Show print statements
- ``-k "test_name"``: Run specific test
- ``--pdb``: Debug on failure
- ``--cov``: Show coverage
- ``--log-cli-level=DEBUG``: Detailed logging

Troubleshooting Tests
-------------------

Common Issues
~~~~~~~~~~~~

1. Blockchain Connection Issues:

   - Ensure Hardhat node is running
   - Check contract deployment
   - Verify account has test ETH

2. IPFS Connection Issues:

   - Confirm IPFS daemon is running
   - Check IPFS API port accessibility
   - Verify Gateway connectivity

3. Test Timeouts:

   - Increase timeouts in ``conftest.py``
   - Check network connectivity
   - Consider resource constraints

4. Database Issues:

   - Ensure clean test database
   - Check migrations
   - Verify permissions

Solutions
~~~~~~~~

For Blockchain Issues:

.. code-block:: console

    # Reset Hardhat node
    $ npx hardhat clean
    $ npx hardhat node

    # Verify deployment
    $ npx hardhat test --network localhost

For IPFS Issues:

.. code-block:: console

    # Reset IPFS
    $ ipfs repo gc
    $ ipfs daemon --offline  # Test without network

    # Check IPFS connection
    $ curl -X POST http://127.0.0.1:5001/api/v0/version

For Test Database:

.. code-block:: console

    # Reset test database
    $ python manage.py flush --database=test

Writing Tests
-----------

Guidelines for writing tests:

1. Test Structure:

   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)
   - Use appropriate fixtures
   - Handle cleanup

2. Mock Usage:

   - Mock external services
   - Use appropriate mock data
   - Clean up mocks

3. Assertions:

   - Use specific assertions
   - Check error cases
   - Verify side effects

Example Test:

.. code-block:: python

    def test_consent_creation(consent_manager, sample_agreement_data):
        """Test consent agreement creation."""
        # Arrange
        purpose = ConsentPurpose(
            id="test-purpose",
            name="Test Purpose",
            description="Test Description"
        )
        
        # Act
        agreement = consent_manager.create_agreement(
            subject_id="test-subject",
            processor_id="test-processor",
            purposes=[purpose]
        )
        
        # Assert
        assert agreement.id is not None
        assert agreement.status == "active"
        assert len(agreement.purposes) == 1

Continuous Integration
-------------------

OConsent uses GitHub Actions for CI. The workflow includes:

1. Unit Tests:
   - Python 3.8, 3.9, 3.10
   - Multiple OS (Ubuntu, MacOS)

2. Integration Tests:
   - Scheduled runs
   - Main branch only

3. Coverage Reports:
   - Minimum 80% coverage
   - Report generation

View CI status at `GitHub Actions <https://github.com/oconsent/oconsent/actions>`_.