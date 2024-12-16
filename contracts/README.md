# OConsent Smart Contracts

This directory contains the smart contracts for the OConsent (Open Consent Protocol) implementation. The contracts provide a decentralized consent management system with advanced features like zero-knowledge proofs, purpose-based access control, and multi-party consent chains.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Contract Descriptions](#contract-descriptions)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Network Configuration](#network-configuration)
- [Security Considerations](#security-considerations)
- [Gas Optimization](#gas-optimization)
- [Contributing](#contributing)

## Architecture Overview

The OConsent smart contracts are built on a modular architecture consisting of three main components:

1. **ConsentRegistry**: Core contract managing consent agreements and their lifecycle
2. **ConsentVerifier**: Validation and verification of consent states
3. **ConsentBatchOperations**: Batch processing capabilities for scalability

```
┌─────────────────┐     ┌─────────────────┐
│ ConsentRegistry │◄────┤ConsentVerifier  │
└────────┬────────┘     └─────────────────┘
         │
         │             ┌─────────────────┐
         └────────────►│BatchOperations  │
                      └─────────────────┘
```

## Contract Descriptions

### ConsentRegistry.sol
- Core contract managing consent agreements
- Features:
  - Agreement creation and management
  - Purpose-based consent tracking
  - Time-based validity
  - Event emission for tracking
  - Access control mechanisms
- Key Functions:
  ```solidity
  function createAgreement(
      string memory id,
      address subject,
      address processor,
      Purpose[] memory purposes,
      uint256 validFrom,
      uint256 validUntil,
      string memory metadataHash
  ) public returns (bool)
  ```

### ConsentVerifier.sol
- Handles consent verification logic
- Features:
  - Consent state validation
  - Purpose verification
  - Time-based checks
  - Integration with Registry
- Key Functions:
  ```solidity
  function verifyConsent(
      string memory agreementId,
      string memory purposeId,
      address processor
  ) public view returns (bool)
  ```

### ConsentBatchOperations.sol
- Enables batch processing of consent operations
- Features:
  - Bulk agreement creation
  - Batch verification
  - Error handling
  - Gas optimization
- Key Functions:
  ```solidity
  function batchVerifyConsents(
      string[] memory agreementIds,
      string[] memory purposeIds,
      address[] memory processors
  ) public view returns (BatchVerificationResult[] memory)
  ```

## Development Setup

### Prerequisites
- Node.js (v14+)
- npm or yarn
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/oconsent.git
cd oconsent/contracts
```

2. Install dependencies:
```bash
npm install
```

3. Install Hardhat globally (optional):
```bash
npm install -g hardhat
```

4. Set up environment:
```bash
cp .env.template .env
# Edit .env with your configuration
```

### Required Dependencies
```json
{
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
    "@openzeppelin/contracts": "^4.9.0",
    "hardhat": "^2.17.0",
    "dotenv": "^16.0.3",
    "hardhat-gas-reporter": "^1.0.9"
  }
}
```


## Working with Hardhat Node

### Starting Hardhat Node

1. **Start Local Node**:
```bash
npx hardhat node
```
This will start a local Ethereum node with the following features:
- JSON-RPC server at http://127.0.0.1:8545/
- Multiple pre-funded accounts for testing
- Real-time console output of transactions and events
- Chain ID: 31337

2. **Default Accounts**:
The node comes with 20 accounts pre-funded with 10000 ETH each. The private keys and addresses will be displayed in the console output.

Example output:
```
Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/

Accounts
========
Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000 ETH)
Private Key: 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d

[...]
```

### Interacting with Local Node

1. **Deploy Contracts**:
Open a new terminal and run:
```bash
npx hardhat run scripts/deploy.js --network localhost
```

2. **Run Tests Against Local Node**:
```bash
npx hardhat test --network localhost
```

3. **Console Interaction**:
```bash
npx hardhat console --network localhost
```

### Network Configuration for Local Node
In your `hardhat.config.js`:
```javascript
module.exports = {
  networks: {
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337
    }
  }
};
```

### Troubleshooting Local Node

1. **Port Already in Use**:
If port 8545 is already in use:
```bash
lsof -i :8545  # Find process using the port
kill -9 <PID>  # Kill the process
```

2. **Reset Local Node**:
To reset the node to its initial state:
```bash
# Stop the current node
ctrl + c

# Clear cache and artifacts
npx hardhat clean

# Restart the node
npx hardhat node
```

3. **Common Issues**:
- Make sure no other Ethereum node (like Ganache) is running
- Check if the network in hardhat.config.js matches the running node
- Verify the chainId matches (31337 for hardhat node)

### Development Workflow with Local Node

1. **Start Development Session**:
```bash
# Terminal 1: Start node
npx hardhat node

# Terminal 2: Deploy contracts
npx hardhat run scripts/deploy.js --network localhost

# Terminal 3: Run tests or development console
npx hardhat console --network localhost
```

2. **Watch Contract Events**:
The node console will show:
- Transaction details
- Event emissions
- Contract deployments
- Gas usage

3. **Automated Tasks**:
Create custom tasks in `hardhat.config.js`:
```javascript
task("accounts", "Prints the list of accounts", async (taskArgs, hre) => {
  const accounts = await hre.ethers.getSigners();
  for (const account of accounts) {
    console.log(account.address);
  }
});
```
Run with:
```bash
npx hardhat accounts --network localhost
```

## Testing

### Test Files Structure

1. **ConsentRegistry.test.js**
   - Basic agreement creation and management
   - Purpose handling
   - Access control validation
   - Event emission verification

2. **ConsentVerifier.test.js**
   - Consent verification logic
   - Time-based validation
   - Purpose verification
   - Integration with Registry

3. **ComplexIntegration.test.js**
   - Multi-party consent chains
   - Time-based scenarios
   - Complex state transitions

4. **AdvancedScenarios.test.js**
   - Multiple purpose updates
   - Agreement expiration
   - Edge cases for access control

### Running Tests

```bash
# Run all tests
npx hardhat test

# Run specific test file
npx hardhat test test/ConsentRegistry.test.js

# Run with gas reporting
REPORT_GAS=true npx hardhat test

# Run with coverage
npx hardhat coverage
```

## Deployment

### Configuration
Create a `.env` file with:
```env
SEPOLIA_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR-API-KEY
MAINNET_URL=https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY
POLYGON_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR-API-KEY
PRIVATE_KEY=your-private-key-here
ETHERSCAN_API_KEY=your-etherscan-api-key
```

### Deployment Scripts

1. **Local Development**:
```bash
npx hardhat run scripts/deploy.js --network localhost
```

2. **Test Networks**:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

3. **Production Networks**:
```bash
npx hardhat run scripts/deploy.js --network mainnet
```

### Verification
Contracts will be automatically verified on Etherscan for supported networks.

## Network Configuration

The project supports multiple networks through `hardhat.config.js`:

- Local Development (Hardhat Network)
- Local Node (localhost)
- Sepolia Testnet
- Ethereum Mainnet
- Polygon Network

Example configuration:
```javascript
networks: {
    hardhat: {
        chainId: 31337
    },
    localhost: {
        url: "http://127.0.0.1:8545"
    },
    sepolia: {
        url: process.env.SEPOLIA_URL,
        accounts: [process.env.PRIVATE_KEY]
    }
    // ... other networks
}
```

## Security Considerations

1. **Access Control**
   - Role-based access control for sensitive operations
   - Proper validation of callers
   - Time-based restrictions

2. **Data Privacy**
   - On-chain data minimization
   - Proper event emission
   - Metadata handling

3. **Smart Contract Security**
   - Reentrancy protection
   - Integer overflow protection
   - Proper error handling

## Gas Optimization

The contracts implement several gas optimization techniques:

1. **Batch Processing**
   - Bulk operations for reduced gas costs
   - Optimized data structures

2. **Storage Optimization**
   - Packed storage slots
   - Minimal on-chain data

3. **Computation Efficiency**
   - View functions for read operations
   - Optimized loops and calculations

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

1. **Code Style**
   - Follow Solidity style guide
   - Use proper documentation
   - Include NatSpec comments

2. **Testing**
   - Write comprehensive tests
   - Maintain test coverage
   - Document test scenarios

3. **Documentation**
   - Update README.md
   - Document new features
   - Include deployment instructions

