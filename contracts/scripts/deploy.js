const hre = require("hardhat");

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);

    // Deploy Registry
    const ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
    const registry = await ConsentRegistry.deploy();
    await registry.waitForDeployment();
    const registryAddress = await registry.getAddress();
    console.log("ConsentRegistry deployed to:", registryAddress);

    // Write address to file for tests
    const fs = require('fs');
    fs.writeFileSync(
        '../.test-contract-address',
        registryAddress
    );


    // Deploy Verifier
    const ConsentVerifier = await ethers.getContractFactory("ConsentVerifier");
    const verifier = await ConsentVerifier.deploy(await registry.getAddress());
    await verifier.waitForDeployment();
    console.log("ConsentVerifier deployed to:", await verifier.getAddress());

    // Deploy BatchOperations
    const ConsentBatchOperations = await ethers.getContractFactory("ConsentBatchOperations");
    const batchOps = await ConsentBatchOperations.deploy(
        await registry.getAddress(),
        await verifier.getAddress()
    );
    await batchOps.waitForDeployment();
    console.log("ConsentBatchOperations deployed to:", await batchOps.getAddress());

    // Verify contracts on explorer (if not localhost)
    if (network.name !== "hardhat" && network.name !== "localhost") {
        console.log("Verifying contracts on Etherscan...");
        await verify(await registry.getAddress(), []);
        await verify(await verifier.getAddress(), [await registry.getAddress()]);
        await verify(await batchOps.getAddress(), [
            await registry.getAddress(),
            await verifier.getAddress()
        ]);
    }
}

async function verify(contractAddress, args) {
    try {
        await hre.run("verify:verify", {
            address: contractAddress,
            constructorArguments: args,
        });
    } catch (e) {
        console.log(`Verification failed for ${contractAddress}: ${e.message}`);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });