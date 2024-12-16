// test/ComplexIntegration.test.js

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

            // Create agreements for data flow: subject -> processor1 -> processor2
            const agreements = [
                {
                    id: "agreement-p1",
                    subject: subject1.address,
                    processor: processor1.address,
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
                },
                {
                    id: "agreement-p2",
                    subject: subject1.address,
                    processor: processor2.address,
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
                }
            ];

            // Batch create agreements
            const batchResults = await batchOps.batchCreateAgreements(
                agreements.map(a => a.id),
                agreements.map(a => a.subject),
                agreements.map(a => a.processor),
                agreements.map(a => a.purposes),
                agreements.map(a => a.validFrom),
                agreements.map(a => a.validUntil),
                agreements.map(a => a.metadataHash)
            );

            // Verify all agreements were created
            batchResults.forEach(result => expect(result.success).to.be.true);

            // Verify consent chain
            const verificationResults = await batchOps.batchVerifyConsents(
                ["agreement-p1", "agreement-p2"],
                ["collect-data", "process-data"],
                [processor1.address, processor2.address]
            );

            verificationResults.forEach(result => expect(result.isValid).to.be.true);

            // Revoke first agreement and verify chain break
            await registry.connect(subject1).updateAgreement(
                "agreement-p1",
                "revoked",
                "proof-123",
                "timestamp-123"
            );

            const verificationAfterRevoke = await batchOps.batchVerifyConsents(
                ["agreement-p1", "agreement-p2"],
                ["collect-data", "process-data"],
                [processor1.address, processor2.address]
            );

            expect(verificationAfterRevoke[0].isValid).to.be.false;
            expect(verificationAfterRevoke[1].isValid).to.be.true; // Second agreement still valid
        });

        it("Should handle cascading purpose updates", async function () {
            const currentTime = await time.latest();
            const baseAgreement = {
                id: "cascade-test",
                subject: subject1.address,
                processor: processor1.address,
                purposes: [{
                    id: "base-purpose",
                    name: "Base Processing",
                    description: "Initial processing",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                validFrom: currentTime,
                validUntil: currentTime + 31536000,
                metadataHash: "QmHash1"
            };

            // Create initial agreement
            await registry.connect(processor1).createAgreement(
                baseAgreement.id,
                baseAgreement.subject,
                baseAgreement.processor,
                baseAgreement.purposes,
                baseAgreement.validFrom,
                baseAgreement.validUntil,
                baseAgreement.metadataHash
            );

            // Add multiple related purposes
            const newPurposes = [
                {
                    id: "derived-1",
                    name: "Derived Processing 1",
                    description: "First derived processing",
                    retentionPeriod: 1296000,
                    createdAt: currentTime
                },
                {
                    id: "derived-2",
                    name: "Derived Processing 2",
                    description: "Second derived processing",
                    retentionPeriod: 1296000,
                    createdAt: currentTime
                }
            ];

            for (const purpose of newPurposes) {
                await registry.connect(processor1).addPurpose(
                    baseAgreement.id,
                    purpose
                );
            }

            // Verify all purposes
            const verificationResults = await batchOps.batchVerifyConsents(
                Array(3).fill(baseAgreement.id),
                ["base-purpose", "derived-1", "derived-2"],
                Array(3).fill(processor1.address)
            );

            verificationResults.forEach(result => expect(result.isValid).to.be.true);

            // Test cascading updates
            await registry.connect(subject1).updateAgreement(
                baseAgreement.id,
                "restricted",
                "proof-123",
                "timestamp-123"
            );

            const storedAgreement = await registry.getAgreement(baseAgreement.id);
            expect(storedAgreement.status).to.equal("restricted");

            // Verify all purposes are affected
            const verificationAfterUpdate = await batchOps.batchVerifyConsents(
                Array(3).fill(baseAgreement.id),
                ["base-purpose", "derived-1", "derived-2"],
                Array(3).fill(processor1.address)
            );

            verificationAfterUpdate.forEach(result => expect(result.isValid).to.be.false);
        });

        it("Should handle complex time-based scenarios", async function () {
            const currentTime = await time.latest();
            
            // Create agreements with different time windows
            const timeBasedAgreements = [
                {
                    id: "immediate-agreement",
                    subject: subject1.address,
                    processor: processor1.address,
                    purposes: [{
                        id: "immediate-purpose",
                        name: "Immediate Processing",
                        description: "Start immediately",
                        retentionPeriod: 3600,
                        createdAt: currentTime
                    }],
                    validFrom: currentTime,
                    validUntil: currentTime + 3600,
                    metadataHash: "QmHash1"
                },
                {
                    id: "future-agreement",
                    subject: subject1.address,
                    processor: processor1.address,
                    purposes: [{
                        id: "future-purpose",
                        name: "Future Processing",
                        description: "Start in future",
                        retentionPeriod: 3600,
                        createdAt: currentTime
                    }],
                    validFrom: currentTime + 1800, // Start in 30 minutes
                    validUntil: currentTime + 5400, // Valid for 1.5 hours after start
                    metadataHash: "QmHash2"
                }
            ];

            // Create agreements
            await batchOps.batchCreateAgreements(
                timeBasedAgreements.map(a => a.id),
                timeBasedAgreements.map(a => a.subject),
                timeBasedAgreements.map(a => a.processor),
                timeBasedAgreements.map(a => a.purposes),
                timeBasedAgreements.map(a => a.validFrom),
                timeBasedAgreements.map(a => a.validUntil),
                timeBasedAgreements.map(a => a.metadataHash)
            );

            // Verify initial state
            let verificationResults = await batchOps.batchVerifyConsents(
                ["immediate-agreement", "future-agreement"],
                ["immediate-purpose", "future-purpose"],
                [processor1.address, processor1.address]
            );

            expect(verificationResults[0].isValid).to.be.true;  // Immediate should be valid
            expect(verificationResults[1].isValid).to.be.false; // Future should not be valid yet

            // Move time forward 35 minutes
            await time.increase(2100);

            // Verify state after time shift
            verificationResults = await batchOps.batchVerifyConsents(
                ["immediate-agreement", "future-agreement"],
                ["immediate-purpose", "future-purpose"],
                [processor1.address, processor1.address]
            );

            expect(verificationResults[0].isValid).to.be.true;  // Immediate should still be valid
            expect(verificationResults[1].isValid).to.be.true;  // Future should now be valid

            // Move time forward another hour
            await time.increase(3600);

            // Verify final state
            verificationResults = await batchOps.batchVerifyConsents(
                ["immediate-agreement", "future-agreement"],
                ["immediate-purpose", "future-purpose"],
                [processor1.address, processor1.address]
            );

            expect(verificationResults[0].isValid).to.be.false; // Immediate should have expired
            expect(verificationResults[1].isValid).to.be.true;  // Future should still be valid
        });
    });
});