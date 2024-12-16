// test/Integration.test.js

const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ConsentRegistry-Verifier Integration", function () {
  let registry;
  let verifier;
  let owner;
  let subject;
  let processor;
  let addrs;

  beforeEach(async function () {
    [owner, subject, processor, ...addrs] = await ethers.getSigners();

    // Deploy Registry
    const ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
    registry = await ConsentRegistry.deploy();
    await registry.waitForDeployment();

    // Deploy Verifier with Registry address
    const ConsentVerifier = await ethers.getContractFactory("ConsentVerifier");
    verifier = await ConsentVerifier.deploy(await registry.getAddress());
    await verifier.waitForDeployment();
  });

  describe("Lifecycle Integration", function () {
    it("Should handle full consent lifecycle", async function () {
      const currentTime = await time.latest();
      
      // 1. Create Agreement
      const agreement = {
        id: "lifecycle-test",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis",
          retentionPeriod: 2592000,
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 31536000,
        metadataHash: "QmHash123"
      };

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      // 2. Verify initial state
      let isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );
      expect(isValid).to.be.true;

      // 3. Add new purpose
      const newPurpose = {
        id: "purpose-2",
        name: "Marketing",
        description: "Email campaigns",
        retentionPeriod: 7776000,
        createdAt: currentTime
      };

      await registry.connect(processor).addPurpose(agreement.id, newPurpose);

      // 4. Verify new purpose
      isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-2",
        processor.address
      );
      expect(isValid).to.be.true;

      // 5. Check purpose details
      const purposeDetails = await verifier.getPurposeDetails(
        agreement.id,
        "purpose-2"
      );
      expect(purposeDetails.name).to.equal("Marketing");
      expect(purposeDetails.description).to.equal("Email campaigns");
      expect(purposeDetails.retentionPeriod).to.equal(7776000);

      // 6. Revoke consent
      await registry.connect(subject).updateAgreement(
        agreement.id,
        "revoked",
        "proof-123",
        "timestamp-123"
      );

      // 7. Verify revoked state
      isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-2",
        processor.address
      );
      expect(isValid).to.be.false;
    });

    it("Should handle concurrent agreements for same subject", async function () {
      const currentTime = await time.latest();
      
      // Create two agreements for the same subject
      const agreement1 = {
        id: "agreement-1",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis",
          retentionPeriod: 2592000,
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 31536000,
        metadataHash: "QmHash123"
      };

      const agreement2 = {
        id: "agreement-2",
        purposes: [{
          id: "purpose-2",
          name: "Marketing",
          description: "Email marketing",
          retentionPeriod: 2592000,
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 31536000,
        metadataHash: "QmHash456"
      };

      // Create both agreements
      await registry.connect(processor).createAgreement(
        agreement1.id,
        subject.address,
        processor.address,
        agreement1.purposes,
        agreement1.validFrom,
        agreement1.validUntil,
        agreement1.metadataHash
      );

      await registry.connect(processor).createAgreement(
        agreement2.id,
        subject.address,
        processor.address,
        agreement2.purposes,
        agreement2.validFrom,
        agreement2.validUntil,
        agreement2.metadataHash
      );

      // Verify both are valid
      let isValid1 = await verifier.verifyConsent(
        agreement1.id,
        "purpose-1",
        processor.address
      );
      let isValid2 = await verifier.verifyConsent(
        agreement2.id,
        "purpose-2",
        processor.address
      );
      
      expect(isValid1).to.be.true;
      expect(isValid2).to.be.true;

      // Revoke one agreement
      await registry.connect(subject).updateAgreement(
        agreement1.id,
        "revoked",
        "proof-123",
        "timestamp-123"
      );

      // Verify states after revocation
      isValid1 = await verifier.verifyConsent(
        agreement1.id,
        "purpose-1",
        processor.address
      );
      isValid2 = await verifier.verifyConsent(
        agreement2.id,
        "purpose-2",
        processor.address
      );
      
      expect(isValid1).to.be.false;
      expect(isValid2).to.be.true;
    });

    it("Should handle purpose retention periods", async function () {
      const currentTime = await time.latest();
      
      // Create agreement with short retention period
      const agreement = {
        id: "retention-test",
        purposes: [{
          id: "purpose-1",
          name: "Short-term",
          description: "Short retention test",
          retentionPeriod: 3600, // 1 hour
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 31536000,
        metadataHash: "QmHash123"
      };

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      // Verify initial state
      let isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );
      expect(isValid).to.be.true;

      // Move time forward beyond retention period
      await time.increase(3600 + 1);

      // Get purpose details
      const purposeDetails = await verifier.getPurposeDetails(
        agreement.id,
        "purpose-1"
      );
      expect(purposeDetails.retentionPeriod).to.equal(3600);

      // Verify consent is still valid (retention period is informational)
      isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );
      expect(isValid).to.be.true;
    });
  });

  describe("Error Handling Integration", function () {
    it("Should handle verification of partially valid agreements", async function () {
      const currentTime = await time.latest();
      
      // Create agreement with multiple purposes
      const agreement = {
        id: "multi-purpose",
        purposes: [
          {
            id: "purpose-1",
            name: "Analytics",
            description: "Data analysis",
            retentionPeriod: 2592000,
            createdAt: currentTime
          },
          {
            id: "purpose-2",
            name: "Marketing",
            description: "Email marketing",
            retentionPeriod: 2592000,
            createdAt: currentTime
          }
        ],
        validFrom: currentTime,
        validUntil: currentTime + 31536000,
        metadataHash: "QmHash123"
      };

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      // Verify non-existent purpose
      const isValidNonExistent = await verifier.verifyConsent(
        agreement.id,
        "non-existent-purpose",
        processor.address
      );
      expect(isValidNonExistent).to.be.false;

      // Verify existing purpose
      const isValidExisting = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );
      expect(isValidExisting).to.be.true;

      // Try to get details of non-existent purpose
      await expect(
        verifier.getPurposeDetails(agreement.id, "non-existent-purpose")
      ).to.be.revertedWith("Purpose not found");
    });
  });
});