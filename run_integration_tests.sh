#!/bin/bash
# run_integration_tests.sh

# Store the root project directory
PROJECT_ROOT=$(pwd)

# Change to contracts directory where Hardhat is configured
cd contracts || exit 1
echo "Changed to contracts directory: $(pwd)"

# Start Hardhat node in background
echo "Starting Hardhat node..."
npx hardhat node &
HARDHAT_PID=$!

# Wait for node to start
echo "Waiting for node to start..."
sleep 5

# Deploy contracts
echo "Deploying contracts..."
npx hardhat run scripts/deploy.js --network localhost

# Get deployed contract address
if [ -f "../.test-contract-address" ]; then
    CONTRACT_ADDRESS=$(cat ../.test-contract-address)
    echo "Contract deployed at: $CONTRACT_ADDRESS"
else
    echo "Contract address file not found"
    kill $HARDHAT_PID
    exit 1
fi

# Change back to project root
cd $PROJECT_ROOT || exit 1
echo "Changed back to project root: $(pwd)"

# Run integration tests
echo "Running integration tests..."
pytest -v -m integration --eth-provider="http://localhost:8545" --contract-address="$CONTRACT_ADDRESS"

# Clean up
echo "Cleaning up..."
kill $HARDHAT_PID
rm -f .test-contract-address

echo "Integration tests completed"