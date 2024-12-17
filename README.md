# OConsent Protocol

Open Consent Protocol implementation in Python with Ethereum smart contracts.

## Structure

```
oconsent/
├── oconsent/                     # Main package directory
│   ├── __init__.py              # Package initialization
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── consent.py          # Consent management
│   │   ├── proofs.py           # Proof generation/verification
│   │   └── timestamp.py        # Timestamp services
│   │
│   ├── blockchain/             # Blockchain interactions
│   │   ├── __init__.py
│   │   ├── ethereum.py         # Ethereum client
│   │   ├── bitcoin.py          # Bitcoin timestamping
│   │   └── sidechain.py        # Sidechain operations
│   │
│   ├── crypto/                 # Cryptographic operations
│   │   ├── __init__.py
│   │   ├── zk_proofs.py       # Zero-knowledge proofs
│   │   └── signatures.py       # Digital signatures
│   │
│   ├── storage/               # Storage providers
│   │   ├── __init__.py
│   │   └── providers.py       # IPFS and other storage
│   │
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── logging.py        # Logging setup
│   │   ├── validation.py     # Data validation
│   │   └── errors.py         # Custom exceptions
│   │
│   └── cli/                  # Command-line interface
│       ├── __init__.py
│       └── commands.py       # CLI commands
│
├── contracts/                # Smart contracts
│   ├── package.json         # npm configuration
│   ├── hardhat.config.js    # Hardhat configuration
│   ├── .env                 # Environment variables
│   ├── .env.template        # Template for .env
│   ├── contracts/
│   │   ├── ConsentRegistry.sol
│   │   ├── ConsentVerifier.sol
│   │   └── ConsentBatchOperations.sol
│   ├── test/
│   │   ├── ConsentRegistry.test.js
│   │   ├── ConsentVerifier.test.js
│   │   ├── Integration.test.js
│   │   ├── AdvancedScenarios.test.js
│   │   └── ComplexIntegration.test.js
│   └── scripts/
│       └── deploy.js        # Deployment script
│
├── tests/                   # Python package tests
│   ├── __init__.py
│   ├── test_consent.py
│   ├── test_blockchain.py
│   ├── test_crypto.py
│   └── test_storage.py
│
├── docs/                    # Documentation
│   ├── source/
│   │   ├── conf.py         # Sphinx configuration
│   │   ├── index.rst       # Documentation index
│   │   ├── installation.rst
│   │   ├── usage.rst
│   │   ├── api.rst
│   │   ├── examples.rst
│   │   └── security.rst
│   ├── Makefile            # Documentation build
│   └── requirements.txt    # Doc dependencies
│
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .github/                # GitHub configurations
│   └── workflows/
│       ├── python-package.yml
│       └── contracts-test.yml
│
├── setup.py               # Package setup file
├── setup.cfg             # Package configuration
├── pyproject.toml        # Build system requirements
├── requirements.txt      # Package dependencies
├── requirements_dev.txt  # Development dependencies
├── tox.ini              # Tox configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .gitignore           # Git ignore rules
├── README.md            # Project README
├── LICENSE             # License file
└── CONTRIBUTING.md     # Contributing guidelines
```

Key file purposes:

1. **Package Core (`oconsent/`)**:
   - Core implementation files
   - Module-specific functionality
   - Utility functions and helpers

2. **Smart Contracts (`contracts/`)**:
   - Solidity smart contracts
   - Contract tests
   - Deployment scripts
   - Contract-specific configuration

3. **Tests (`tests/`)**:
   - Python package unit tests
   - Integration tests
   - Test utilities and fixtures

4. **Documentation (`docs/`)**:
   - Sphinx documentation source
   - API documentation
   - Usage examples
   - Security guidelines

5. **Configuration Files**:
   - `setup.py`: Package installation
   - `pyproject.toml`: Build configuration
   - `tox.ini`: Test automation
   - `.pre-commit-config.yaml`: Code quality checks

6. **CI/CD (`.github/`)**:
   - GitHub Actions workflows
   - Automated testing
   - Deployment pipelines

7. **Docker (`docker/`)**:
   - Container definitions
   - Compose configuration
   - Build scripts




## Installation

### Python Package
```bash
pip install -e .
```

### Smart Contracts
```bash
cd contracts
npm install
npx hardhat compile
```

## Development

### Running Tests
Python tests:
```bash
pytest tests/
```

Smart contract tests:
```bash
cd contracts
npx hardhat test
```

### Run only unit tests
```bash
pytest -v -m "not integration"
```

### Run only integration tests
```bash
pytest -v -m integration
```

### Run integration tests with custom Ethereum provider
```bash
pytest -v -m integration --eth-provider="http://localhost:8545"
```


### Run integration tests with specific contract
```bash
pytest -v -m integration --contract-address="0x1234..."
```


### Run all tests
```bash
pytest -v
```

### or, run integration tests with a local Hardhat node (script provided):

```bash
./run_integration_tests.sh
```