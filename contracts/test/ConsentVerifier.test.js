const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ConsentVerifier", function () {
  let ConsentRegistry;
  let ConsentVerifier;
  let registry;
  let verifier;
  let owner;
  let subject;
  let processor;
  let addrs;

  beforeEach(async function () {
    // Get test accounts
    [owner, subject, processor, ...addrs] = await ethers.getSigners();

    // Deploy ConsentRegistry first
    ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
    registry = await ConsentRegistry.deploy();
    await registry.waitForDeployment();

    // Deploy ConsentVerifier with registry address
    ConsentVerifier = await ethers.getContractFactory("ConsentVerifier");
    verifier = await ConsentVerifier.deploy(await registry.getAddress());
    await verifier.waitForDeployment();
  });

  describe("Basic Verification", function () {
    it("Should verify valid consent", async function () {
      const currentTime = await time.latest();
      const agreement = {
        id: "agreement-1",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis",
          retentionPeriod: 2592000, // 30 days
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 31536000, // 1 year
        metadataHash: "QmHash123"
      };

      // Create agreement
      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      // Verify consent
      const isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );

      expect(isValid).to.be.true;
    });

    it("Should return false for non-existent agreement", async function () {
      const isValid = await verifier.verifyConsent(
        "non-existent-id",
        "purpose-1",
        processor.address
      );

      expect(isValid).to.be.false;
    });

    it("Should return false for wrong processor", async function () {
      const currentTime = await time.latest();
      const agreement = {
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

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      const wrongProcessor = addrs[0];
      const isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        wrongProcessor.address
      );

      expect(isValid).to.be.false;
    });
  });

  describe("Time-based Verification", function () {
    it("Should return false for not-yet-valid agreement", async function () {
      const currentTime = await time.latest();
      const agreement = {
        id: "agreement-1",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis",
          retentionPeriod: 2592000,
          createdAt: currentTime
        }],
        validFrom: currentTime + 3600, // Valid 1 hour from now
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

      const isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );

      expect(isValid).to.be.false;
    });

    it("Should return false for expired agreement", async function () {
      const currentTime = await time.latest();
      const agreement = {
        id: "agreement-1",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis",
          retentionPeriod: 2592000,
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + 3600, // Valid for 1 hour
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

      // Move time forward by 2 hours
      await time.increase(7200);

      const isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );

      expect(isValid).to.be.false;
    });
  });

  describe("Purpose Verification", function () {
    it("Should return false for non-existent purpose", async function () {
      const currentTime = await time.latest();
      const agreement = {
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

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      const isValid = await verifier.verifyConsent(
        agreement.id,
        "non-existent-purpose",
        processor.address
      );

      expect(isValid).to.be.false;
    });

    it("Should return purpose details correctly", async function () {
      const currentTime = await time.latest();
      const agreement = {
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

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      const purpose = await verifier.getPurposeDetails(
        agreement.id,
        "purpose-1"
      );

      expect(purpose.name).to.equal("Analytics");
      expect(purpose.description).to.equal("Data analysis");
      expect(purpose.retentionPeriod).to.equal(2592000);
    });

    it("Should revert for non-existent purpose when getting details", async function () {
      const currentTime = await time.latest();
      const agreement = {
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

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      await expect(
        verifier.getPurposeDetails(agreement.id, "non-existent-purpose")
      ).to.be.revertedWith("Purpose not found");
    });
  });

  describe("Status-based Verification", function () {
    it("Should return false for revoked agreement", async function () {
      const currentTime = await time.latest();
      const agreement = {
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

      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      // Revoke agreement
      await registry.connect(subject).updateAgreement(
        agreement.id,
        "revoked",
        "proof-123",
        "timestamp-123"
      );

      const isValid = await verifier.verifyConsent(
        agreement.id,
        "purpose-1",
        processor.address
      );

      expect(isValid).to.be.false;
    });
  });
});