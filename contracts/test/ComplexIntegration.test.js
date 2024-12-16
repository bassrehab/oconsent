const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("Complex Consent Integration", function () {
    let registry;
    let verifier;
    let batchOps;
    let owner;
    let subject1;
    let subject2;
    let processor1;
    let processor2;
    let addrs;

    beforeEach(async function () {
        [owner, subject1, subject2, processor1, processor2, ...addrs] = await ethers.getSigners();

        // Deploy contracts
        const ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
        registry = await ConsentRegistry.deploy();
        await registry.waitForDeployment();

        const ConsentVerifier = await ethers.getContractFactory("ConsentVerifier");
        verifier = await ConsentVerifier.deploy(await registry.getAddress());
        await verifier.waitForDeployment();

        const ConsentBatchOperations = await ethers.getContractFactory("ConsentBatchOperations");
        batchOps = await ConsentBatchOperations.deploy(
            await registry.getAddress(),
            await verifier.getAddress()
        );
        await batchOps.waitForDeployment();
    });

    describe("Complex Multi-Party Scenarios", function () {
        it("Should handle multi-processor consent chain", async function () {
            const currentTime = await time.latest();

            // Create individual agreements instead of batch
            const agreement1 = {
                id: "agreement-p1",
                purposes: [{
                    id: "collect-data",
                    name: "Data Collection",
                    description: "Initial data collection",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                validFrom: currentTime,
                validUntil: currentTime + 31536000,
                metadataHash: "QmHash1"
            };

            const agreement2 = {
                id: "agreement-p2",
                purposes: [{
                    id: "process-data",
                    name: "Data Processing",
                    description: "Secondary data processing",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                validFrom: currentTime,
                validUntil: currentTime + 31536000,
                metadataHash: "QmHash2"
            };

            // Create agreements individually
            await registry.connect(processor1).createAgreement(
                agreement1.id,
                subject1.address,
                processor1.address,
                agreement1.purposes,
                agreement1.validFrom,
                agreement1.validUntil,
                agreement1.metadataHash
            );

            await registry.connect(processor2).createAgreement(
                agreement2.id,
                subject1.address,
                processor2.address,
                agreement2.purposes,
                agreement2.validFrom,
                agreement2.validUntil,
                agreement2.metadataHash
            );

            // Verify initial consents
            let isValid1 = await verifier.verifyConsent(
                agreement1.id,
                "collect-data",
                processor1.address
            );
            let isValid2 = await verifier.verifyConsent(
                agreement2.id,
                "process-data",
                processor2.address
            );

            expect(isValid1).to.be.true;
            expect(isValid2).to.be.true;

            // Revoke first agreement
            await registry.connect(subject1).updateAgreement(
                agreement1.id,
                "revoked",
                "proof-123",
                "timestamp-123"
            );

            // Verify after revocation
            isValid1 = await verifier.verifyConsent(
                agreement1.id,
                "collect-data",
                processor1.address
            );
            isValid2 = await verifier.verifyConsent(
                agreement2.id,
                "process-data",
                processor2.address
            );

            expect(isValid1).to.be.false;
            expect(isValid2).to.be.true; // Second agreement still valid
        });

        it("Should handle complex time-based scenarios", async function () {
            // Get current time and log it for debugging
            const currentTime = await time.latest();
            console.log(`Current time: ${currentTime}`);
            
            // Create immediate agreement
            const immediateAgreement = {
                id: "immediate-agreement",
                purposes: [{
                    id: "immediate-purpose",
                    name: "Immediate Processing",
                    description: "Start immediately",
                    retentionPeriod: 3600,
                    createdAt: currentTime
                }],
                validFrom: currentTime,
                validUntil: currentTime + 7200, // 2 hours validity
                metadataHash: "QmHash1"
            };

            // Create future agreement
            const futureAgreement = {
                id: "future-agreement",
                purposes: [{
                    id: "future-purpose",
                    name: "Future Processing",
                    description: "Start in future",
                    retentionPeriod: 3600,
                    createdAt: currentTime
                }],
                validFrom: currentTime + 1800,    // Start in 30 minutes
                validUntil: currentTime + 7200,   // 2 hours from start
                metadataHash: "QmHash2"
            };

            // Create agreements
            console.log("Creating immediate agreement...");
            await registry.connect(processor1).createAgreement(
                immediateAgreement.id,
                subject1.address,
                processor1.address,
                immediateAgreement.purposes,
                immediateAgreement.validFrom,
                immediateAgreement.validUntil,
                immediateAgreement.metadataHash
            );

            console.log("Creating future agreement...");
            await registry.connect(processor1).createAgreement(
                futureAgreement.id,
                subject1.address,
                processor1.address,
                futureAgreement.purposes,
                futureAgreement.validFrom,
                futureAgreement.validUntil,
                futureAgreement.metadataHash
            );

            // Check initial state
            console.log("Checking initial state...");
            let currentBlockTime = await time.latest();
            console.log(`Current block time: ${currentBlockTime}`);

            let immediateValid = await verifier.verifyConsent(
                immediateAgreement.id,
                "immediate-purpose",
                processor1.address
            );
            let futureValid = await verifier.verifyConsent(
                futureAgreement.id,
                "future-purpose",
                processor1.address
            );

            console.log(`Initial verification - Immediate: ${immediateValid}, Future: ${futureValid}`);
            expect(immediateValid).to.be.true;    // Should be valid immediately
            expect(futureValid).to.be.false;      // Should not be valid yet

            // Move time forward 35 minutes (2100 seconds)
            console.log("Moving time forward 35 minutes...");
            await time.increase(2100);
            
            currentBlockTime = await time.latest();
            console.log(`Block time after first increase: ${currentBlockTime}`);

            immediateValid = await verifier.verifyConsent(
                immediateAgreement.id,
                "immediate-purpose",
                processor1.address
            );
            futureValid = await verifier.verifyConsent(
                futureAgreement.id,
                "future-purpose",
                processor1.address
            );

            console.log(`Mid-point verification - Immediate: ${immediateValid}, Future: ${futureValid}`);
            expect(immediateValid).to.be.true;    // Should still be valid
            expect(futureValid).to.be.true;       // Should now be valid

            // Move time forward another 2 hours (7200 seconds)
            console.log("Moving time forward 2 hours...");
            await time.increase(7200);

            currentBlockTime = await time.latest();
            console.log(`Final block time: ${currentBlockTime}`);

            immediateValid = await verifier.verifyConsent(
                immediateAgreement.id,
                "immediate-purpose",
                processor1.address
            );
            futureValid = await verifier.verifyConsent(
                futureAgreement.id,
                "future-purpose",
                processor1.address
            );

            console.log(`Final verification - Immediate: ${immediateValid}, Future: ${futureValid}`);
            expect(immediateValid).to.be.false;   // Should have expired
            expect(futureValid).to.be.false;      // Should have expired
        });
    });
});