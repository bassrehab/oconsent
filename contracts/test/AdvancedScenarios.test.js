const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("Advanced Consent Scenarios", function () {
    let registry;
    let verifier;
    let owner;
    let subject;
    let processor;
    let unauthorizedUser;

    beforeEach(async function () {
        [owner, subject, processor, unauthorizedUser] = await ethers.getSigners();

        const ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
        registry = await ConsentRegistry.deploy();
        await registry.waitForDeployment();

        const ConsentVerifier = await ethers.getContractFactory("ConsentVerifier");
        verifier = await ConsentVerifier.deploy(await registry.getAddress());
        await verifier.waitForDeployment();
    });

    describe("Multiple Purpose Updates", function () {
        it("Should handle multiple purpose updates and versions", async function () {
            const currentTime = await time.latest();
            
            // Create initial agreement with one purpose
            const agreementId = "multiple-purpose-test";
            await registry.connect(processor).createAgreement(
                agreementId,
                subject.address,
                processor.address,
                [{
                    id: "purpose-1",
                    name: "Initial Purpose",
                    description: "First purpose",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                currentTime,
                currentTime + 31536000,
                "QmHash1"
            );

            // Add second purpose
            await registry.connect(processor).addPurpose(
                agreementId,
                {
                    id: "purpose-2",
                    name: "Second Purpose",
                    description: "Second purpose",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }
            );

            // Update first purpose through agreement update
            await registry.connect(processor).updateAgreement(
                agreementId,
                "active",
                "proof-updated",
                "timestamp-updated"
            );

            // Verify both purposes are still valid
            const isValid1 = await verifier.verifyConsent(agreementId, "purpose-1", processor.address);
            const isValid2 = await verifier.verifyConsent(agreementId, "purpose-2", processor.address);
            
            expect(isValid1).to.be.true;
            expect(isValid2).to.be.true;
        });
    });

    describe("Agreement Expiration", function () {
        it("Should correctly handle agreement expiration", async function () {
            const currentTime = await time.latest();
            
            // Create agreement with short expiration
            await registry.connect(processor).createAgreement(
                "expiring-agreement",
                subject.address,
                processor.address,
                [{
                    id: "purpose-1",
                    name: "Short-term Purpose",
                    description: "Expires soon",
                    retentionPeriod: 3600,
                    createdAt: currentTime
                }],
                currentTime,
                currentTime + 3600, // 1 hour validity
                "QmHash1"
            );

            // Verify initially valid
            let isValid = await verifier.verifyConsent(
                "expiring-agreement",
                "purpose-1",
                processor.address
            );
            expect(isValid).to.be.true;

            // Move time forward past expiration
            await time.increase(3601);

            // Verify expired
            isValid = await verifier.verifyConsent(
                "expiring-agreement",
                "purpose-1",
                processor.address
            );
            expect(isValid).to.be.false;
        });

        it("Should handle grace period for renewals", async function () {
            const currentTime = await time.latest();
            const agreementId = "renewable-agreement";
            
            await registry.connect(processor).createAgreement(
                agreementId,
                subject.address,
                processor.address,
                [{
                    id: "purpose-1",
                    name: "Renewable Purpose",
                    description: "Can be renewed",
                    retentionPeriod: 3600,
                    createdAt: currentTime
                }],
                currentTime,
                currentTime + 3600,
                "QmHash1"
            );

            // Move time close to expiration but within grace period
            await time.increase(3500); // 100 seconds before expiration

            // Update agreement to extend validity
            await registry.connect(processor).updateAgreement(
                agreementId,
                "active",
                "renewal-proof",
                "renewal-timestamp"
            );

            // Verify still valid
            const isValid = await verifier.verifyConsent(
                agreementId,
                "purpose-1",
                processor.address
            );
            expect(isValid).to.be.true;
        });
    });

    describe("Access Control Edge Cases", function () {
        it("Should handle unauthorized purpose additions", async function () {
            const currentTime = await time.latest();
            const agreementId = "access-control-test";

            // Create agreement
            await registry.connect(processor).createAgreement(
                agreementId,
                subject.address,
                processor.address,
                [{
                    id: "purpose-1",
                    name: "Initial Purpose",
                    description: "First purpose",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                currentTime,
                currentTime + 31536000,
                "QmHash1"
            );

            // Attempt unauthorized purpose addition
            await expect(
                registry.connect(unauthorizedUser).addPurpose(
                    agreementId,
                    {
                        id: "purpose-2",
                        name: "Unauthorized Purpose",
                        description: "Should fail",
                        retentionPeriod: 2592000,
                        createdAt: currentTime
                    }
                )
            ).to.be.revertedWith("Only processor can add purposes");
        });

        it("Should handle subject-only operations", async function () {
            const currentTime = await time.latest();
            const agreementId = "subject-control-test";

            await registry.connect(processor).createAgreement(
                agreementId,
                subject.address,
                processor.address,
                [{
                    id: "purpose-1",
                    name: "Test Purpose",
                    description: "Test description",
                    retentionPeriod: 2592000,
                    createdAt: currentTime
                }],
                currentTime,
                currentTime + 31536000,
                "QmHash1"
            );

            // Subject can revoke
            await registry.connect(subject).updateAgreement(
                agreementId,
                "revoked",
                "revocation-proof",
                "revocation-timestamp"
            );

            // Processor shouldn't be able to reactivate without subject consent
            await expect(
                registry.connect(processor).updateAgreement(
                    agreementId,
                    "active",
                    "reactivation-proof",
                    "reactivation-timestamp"
                )
            ).to.be.revertedWith("Cannot reactivate revoked agreement");
        });
    });
});