Installation
===========

Prerequisites
------------

Before installing OConsent, ensure you have the following:

* Python 3.8 or later
* Node.js 14 or later (for smart contract development)
* An Ethereum node or provider (like Infura)
* IPFS node (optional, for decentralized storage)

Basic Installation
----------------

Install using pip:

.. code-block:: console

    $ pip install oconsent

For development installation:

.. code-block:: console

    $ git clone https://github.com/yourusername/oconsent.git
    $ cd oconsent
    $ pip install -e .

Smart Contract Setup
------------------

To set up the smart contracts:

.. code-block:: console

    $ cd contracts
    $ npm install
    $ cp .env.template .env
    # Edit .env with your configuration
    $ npx hardhat compile

IPFS Testing Setup
----------------

To run IPFS integration tests, you'll need additional setup:

1. Install and Run IPFS
~~~~~~~~~~~~~~~~~~~~~~~

First, install IPFS daemon:

* Download from `IPFS Installation Guide <https://docs.ipfs.tech/install/>`_
* Or use package manager:

.. code-block:: console

    # On Ubuntu
    $ sudo apt install kubo

    # On MacOS with Homebrew
    $ brew install ipfs

Initialize and start IPFS:

.. code-block:: console

    $ ipfs init
    $ ipfs daemon

2. Configure Environment
~~~~~~~~~~~~~~~~~~~~~~~

Set up environment variables either by exporting directly:

.. code-block:: console

    # Required
    $ export IPFS_NODE=/ip4/127.0.0.1/tcp/5001
    $ export IPFS_GATEWAY=https://ipfs.io

    # Optional - for pinning service testing
    $ export IPFS_PINNING_SERVICE=https://api.pinata.cloud
    $ export IPFS_PINNING_KEY=your_pinning_service_key

Or create a .env file in the project root:

.. code-block:: text

    IPFS_NODE=/ip4/127.0.0.1/tcp/5001
    IPFS_GATEWAY=https://ipfs.io
    IPFS_PINNING_SERVICE=https://api.pinata.cloud
    IPFS_PINNING_KEY=your_pinning_service_key

Troubleshooting
-------------

Common Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Python Dependencies
   
   If you encounter dependency conflicts:

   .. code-block:: console

       $ pip install -e . --no-deps
       $ pip install -r requirements.txt

2. Node.js Issues

   For smart contract compilation errors:

   .. code-block:: console

       $ rm -rf node_modules
       $ npm cache clean --force
       $ npm install

3. IPFS Connection

   If IPFS daemon won't start:

   .. code-block:: console

       $ ipfs init --empty-repo
       $ ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
       $ ipfs daemon --offline  # Test offline first

4. Network Issues

   For connection timeouts:

   .. code-block:: console

       # Test local endpoints
       $ curl http://localhost:8545  # Ethereum
       $ curl http://localhost:5001  # IPFS

       # Check firewall
       $ sudo ufw status
       $ sudo ufw allow 4001  # IPFS swarm
       $ sudo ufw allow 5001  # IPFS API

Environment Setup
~~~~~~~~~~~~~~~

For environment issues:

1. Python Environment:

   .. code-block:: console

       $ python -m venv venv
       $ source venv/bin/activate  # Unix
       $ .\venv\Scripts\activate   # Windows

2. Node Version:

   .. code-block:: console

       $ nvm install 14
       $ nvm use 14

3. Path Issues:

   Add to ~/.bashrc or ~/.zshrc:

   .. code-block:: bash

       export PATH=$PATH:$HOME/.local/bin
       export PATH=$PATH:$HOME/go/bin  # For IPFS

System Requirements
~~~~~~~~~~~~~~~~

- Memory: 4GB minimum (8GB recommended)
- Storage: 1GB for installation, 10GB+ for blockchain data
- Ports: 8545 (Ethereum), 5001 (IPFS API), 4001 (IPFS swarm)

For detailed testing instructions, see :doc:`testing`.