
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ConsentRegistry.sol";

contract ConsentVerifier {
    ConsentRegistry private registry;
    
    constructor(address registryAddress) {
        registry = ConsentRegistry(registryAddress);
    }
    
    function verifyConsent(
        string memory agreementId,
        string memory purposeId,
        address processor
    ) public view returns (bool) {
        // Try to get agreement data, return false if it doesn't exist
        try registry.getAgreement(agreementId) returns (
            ConsentRegistry.ConsentAgreement memory agreement
        ) {
            // Check basic validity
            if (agreement.processor != processor) return false;
            if (keccak256(bytes(agreement.status)) != keccak256(bytes("active"))) return false;
            if (block.timestamp < agreement.validFrom) return false;
            if (agreement.validUntil > 0 && block.timestamp > agreement.validUntil) return false;
            
            // Check purpose
            bool purposeFound = false;
            for (uint i = 0; i < agreement.purposes.length; i++) {
                if (keccak256(bytes(agreement.purposes[i].id)) == keccak256(bytes(purposeId))) {
                    purposeFound = true;
                    break;
                }
            }
            
            return purposeFound;
        } catch {
            return false;
        }
    }
    
    function getPurposeDetails(
        string memory agreementId,
        string memory purposeId
    ) public view returns (
        string memory name,
        string memory description,
        uint256 retentionPeriod
    ) {
        ConsentRegistry.ConsentAgreement memory agreement = registry.getAgreement(agreementId);
        
        for (uint i = 0; i < agreement.purposes.length; i++) {
            if (keccak256(bytes(agreement.purposes[i].id)) == keccak256(bytes(purposeId))) {
                return (
                    agreement.purposes[i].name,
                    agreement.purposes[i].description,
                    agreement.purposes[i].retentionPeriod
                );
            }
        }
        
        revert("Purpose not found");
    }
}