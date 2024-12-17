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