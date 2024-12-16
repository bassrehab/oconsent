const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ConsentRegistry", function () {
  let ConsentRegistry;
  let registry;
  let owner;
  let subject;
  let processor;
  let addrs;

  beforeEach(async function () {
    [owner, subject, processor, ...addrs] = await ethers.getSigners();
    ConsentRegistry = await ethers.getContractFactory("ConsentRegistry");
    registry = await ConsentRegistry.deploy();
    await registry.waitForDeployment();
  });

  describe("Agreement Creation", function () {
    it("Should create a new consent agreement", async function () {
      const currentTime = await time.latest();
      const agreement = {
        id: "agreement-1",
        purposes: [{
          id: "purpose-1",
          name: "Analytics",
          description: "Data analysis for service improvement",
          retentionPeriod: 30 * 24 * 60 * 60,
          createdAt: currentTime
        }],
        validFrom: currentTime,
        validUntil: currentTime + (365 * 24 * 60 * 60),
        metadataHash: "QmHash123"
      };

      await expect(registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      )).to.emit(registry, "AgreementCreated")
        .withArgs(
          agreement.id,
          subject.address,
          processor.address,
          agreement.validFrom,
          agreement.validUntil
        );

      const storedAgreement = await registry.getAgreement(agreement.id);
      expect(storedAgreement.id).to.equal(agreement.id);
      expect(storedAgreement.subject).to.equal(subject.address);
      expect(storedAgreement.processor).to.equal(processor.address);
      expect(storedAgreement.status).to.equal("active");
    });

    it("Should not allow duplicate agreement IDs", async function () {
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
        registry.connect(processor).createAgreement(
          agreement.id,
          subject.address,
          processor.address,
          agreement.purposes,
          agreement.validFrom,
          agreement.validUntil,
          agreement.metadataHash
        )
      ).to.be.revertedWith("Agreement ID already exists");
    });
  });

  describe("Agreement Updates", function () {
    it("Should allow updating agreement status", async function () {
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

      // Listen for the event
      const updateTx = await registry.connect(subject).updateAgreement(
        agreement.id,
        "revoked",
        "proof-123",
        "timestamp-123"
      );

      // Wait for the transaction and check events
      const receipt = await updateTx.wait();
      const updateEvent = receipt.logs[0];
      
      // Get the decoded event data
      const iface = registry.interface;
      const decodedEvent = iface.parseLog(updateEvent);
      
      // Verify the event data
      expect(decodedEvent.name).to.equal("AgreementUpdated");
      expect(decodedEvent.args[0]).to.equal(agreement.id);
      expect(decodedEvent.args[1]).to.equal("revoked");
      
      // Verify the stored data
      const storedAgreement = await registry.getAgreement(agreement.id);
      expect(storedAgreement.status).to.equal("revoked");
      expect(storedAgreement.proofId).to.equal("proof-123");
      expect(storedAgreement.timestampProof).to.equal("timestamp-123");
    });

    it("Should only allow agreement participants to update", async function () {
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

      const nonParticipant = addrs[0];
      await expect(
        registry.connect(nonParticipant).updateAgreement(
          agreement.id,
          "revoked",
          "proof-123",
          "timestamp-123"
        )
      ).to.be.revertedWith("Not authorized");
    });
  });

  describe("Purpose Management", function () {
    it("Should allow adding new purposes", async function () {
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

      // Create initial agreement
      await registry.connect(processor).createAgreement(
        agreement.id,
        subject.address,
        processor.address,
        agreement.purposes,
        agreement.validFrom,
        agreement.validUntil,
        agreement.metadataHash
      );

      const newPurpose = {
        id: "purpose-2",
        name: "Marketing",
        description: "Email marketing",
        retentionPeriod: 7776000,
        createdAt: currentTime
      };

      // We'll get the current block timestamp
      const blockTimestamp = await time.latest();

      // Add new purpose
      const tx = await registry.connect(processor).addPurpose(agreement.id, newPurpose);
      
      // Verify the event emission with all three parameters
      await expect(tx)
        .to.emit(registry, "PurposeAdded")
        .withArgs(agreement.id, newPurpose.id, blockTimestamp + 1); // +1 because the transaction will be in the next block

      // Verify the stored data
      const storedAgreement = await registry.getAgreement(agreement.id);
      expect(storedAgreement.purposes.length).to.equal(2);
      expect(storedAgreement.purposes[1].id).to.equal(newPurpose.id);
      expect(storedAgreement.purposes[1].name).to.equal(newPurpose.name);
      expect(storedAgreement.purposes[1].description).to.equal(newPurpose.description);
      expect(storedAgreement.purposes[1].retentionPeriod).to.equal(newPurpose.retentionPeriod);
    });

    
    it("Should only allow processor to add purposes", async function () {
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
  
        // Create initial agreement
        await registry.connect(processor).createAgreement(
          agreement.id,
          subject.address,
          processor.address,
          agreement.purposes,
          agreement.validFrom,
          agreement.validUntil,
          agreement.metadataHash
        );
  
        const newPurpose = {
          id: "purpose-2",
          name: "Marketing",
          description: "Email marketing",
          retentionPeriod: 7776000,
          createdAt: currentTime
        };
  
        // Try to add purpose as non-processor
        await expect(
          registry.connect(subject).addPurpose(agreement.id, newPurpose)
        ).to.be.revertedWith("Only processor can add purposes");
      });
    });
  });