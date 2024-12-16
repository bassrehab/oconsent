# OConsent Protocol

Open Consent Protocol implementation in Python with Ethereum smart contracts.

## Structure
```
oconsent/
├── oconsent/          # Python package
├── contracts/         # Smart contracts
├── tests/            # Python tests
└── docs/             # Documentation
```

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
