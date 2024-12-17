Troubleshooting
=============

Common Issues
-----------

Smart Contract Connection Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're experiencing issues connecting to the smart contracts:

1. Check your network configuration
2. Verify contract addresses
3. Ensure you have sufficient funds for gas
4. Check network status

Example of connection troubleshooting:

.. code-block:: python

    from oconsent.blockchain.ethereum import EthereumClient
    from web3 import Web3

    # Test connection
    client = EthereumClient(
        provider_url='http://localhost:8545',
        contract_address='0x...'
    )

    try:
        # Check Web3 connection
        if not client.web3.is_connected():
            print("Failed to connect to Ethereum node")
            
        # Check contract
        if not client.contract:
            print("Failed to load contract")
            
    except Exception as e:
        print(f"Error: {str(e)}")

Transaction Failures
~~~~~~~~~~~~~~~~

Common reasons for transaction failures:

1. Insufficient gas
2. Network congestion
3. Invalid parameters
4. Authorization issues

Debug example:

.. code-block:: python

    try:
        agreement = consent_manager.create_agreement(...)
    except Exception as e:
        if "gas required exceeds allowance" in str(e):
            print("Insufficient gas. Try increasing gas limit")
        elif "nonce too low" in str(e):
            print("Transaction nonce issue. Try resetting account nonce")
        else:
            print(f"Unknown error: {str(e)}")