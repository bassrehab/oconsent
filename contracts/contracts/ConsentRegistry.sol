
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract ConsentRegistry is Ownable, Pausable {
    using Counters for Counters.Counter;
    
    // Structs
    struct Purpose {
        string id;
        string name;
        string description;
        uint256 retentionPeriod;
        uint256 createdAt;
    }
    
    struct ConsentAgreement {
        string id;
        address subject;
        address processor;
        Purpose[] purposes;
        uint256 validFrom;
        uint256 validUntil;
        string metadataHash;
        string status;
        string proofId;
        string timestampProof;
    }
    
    // State variables
    mapping(string => ConsentAgreement) private agreements;
    mapping(address => string[]) private subjectAgreements;
    mapping(address => string[]) private processorAgreements;
    Counters.Counter private agreementCounter;
    
    // Events
    event AgreementCreated(
        string id,
        address indexed subject,
        address indexed processor,
        uint256 validFrom,
        uint256 validUntil
    );
    
    event AgreementUpdated(
        string id,
        string status,
        uint256 timestamp
    );
    
    event PurposeAdded(
        string agreementId,
        string purposeId,
        uint256 timestamp
    );
    
    // Modifiers
    modifier agreementExists(string memory id) {
        require(
            bytes(agreements[id].id).length > 0,
            "Agreement does not exist"
        );
        _;
    }
    
    modifier onlyParticipant(string memory id) {
        require(
            msg.sender == agreements[id].subject ||
            msg.sender == agreements[id].processor,
            "Not authorized"
        );
        _;
    }
    
    // Functions
    function createAgreement(
        string memory id,
        address subject,
        address processor,
        Purpose[] memory purposes,
        uint256 validFrom,
        uint256 validUntil,
        string memory metadataHash
    ) public whenNotPaused returns (bool) {
        require(
            bytes(agreements[id].id).length == 0,
            "Agreement ID already exists"
        );
        
        ConsentAgreement storage agreement = agreements[id];
        agreement.id = id;
        agreement.subject = subject;
        agreement.processor = processor;
        agreement.validFrom = validFrom;
        agreement.validUntil = validUntil;
        agreement.metadataHash = metadataHash;
        agreement.status = "active";
        
        for (uint i = 0; i < purposes.length; i++) {
            agreement.purposes.push(purposes[i]);
        }
        
        subjectAgreements[subject].push(id);
        processorAgreements[processor].push(id);
        agreementCounter.increment();
        
        emit AgreementCreated(
            id,
            subject,
            processor,
            validFrom,
            validUntil
        );
        
        return true;
    }
    
    function updateAgreement(
        string memory id,
        string memory status,
        string memory proofId,
        string memory timestampProof
    ) public whenNotPaused agreementExists(id) onlyParticipant(id) returns (bool) {
        ConsentAgreement storage agreement = agreements[id];

        if (keccak256(bytes(agreement.status)) == keccak256(bytes("revoked")) && 
            keccak256(bytes(status)) == keccak256(bytes("active"))) {
            revert("Cannot reactivate revoked agreement");
        }

        agreement.status = status;
        agreement.proofId = proofId;
        agreement.timestampProof = timestampProof;
        
        emit AgreementUpdated(id, status, block.timestamp);
        
        return true;
    }
    
    function addPurpose(
        string memory agreementId,
        Purpose memory purpose
    ) public whenNotPaused agreementExists(agreementId) returns (bool) {
        require(
            msg.sender == agreements[agreementId].processor,
            "Only processor can add purposes"
        );
        
        agreements[agreementId].purposes.push(purpose);
        
        emit PurposeAdded(
            agreementId,
            purpose.id,
            block.timestamp
        );
        
        return true;
    }
    
    function getAgreement(
        string memory id
    ) public view agreementExists(id) returns (ConsentAgreement memory) {
        return agreements[id];
    }
    
    function getSubjectAgreements(
        address subject
    ) public view returns (string[] memory) {
        return subjectAgreements[subject];
    }
    
    function getProcessorAgreements(
        address processor
    ) public view returns (string[] memory) {
        return processorAgreements[processor];
    }
    
    function pause() public onlyOwner {
        _pause();
    }
    
    function unpause() public onlyOwner {
        _unpause();
    }
}