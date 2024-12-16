const hre = require("hardhat");

async function main() {
  const ConsentRegistry = await hre.ethers.getContractFactory("ConsentRegistry");
  const registry = await ConsentRegistry.deploy();
  await registry.deployed();

  console.log("ConsentRegistry deployed to:", registry.address);

  const ConsentVerifier = await hre.ethers.getContractFactory("ConsentVerifier");
  const verifier = await ConsentVerifier.deploy(registry.address);
  await verifier.deployed();

  console.log("ConsentVerifier deployed to:", verifier.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
