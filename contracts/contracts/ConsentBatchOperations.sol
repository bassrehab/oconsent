// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ConsentRegistry.sol";
import "./ConsentVerifier.sol";

contract ConsentBatchOperations {
    ConsentRegistry private registry;
    ConsentVerifier private verifier;
    
    constructor(address registryAddress, address verifierAddress) {
        registry = ConsentRegistry(registryAddress);
        verifier = ConsentVerifier(verifierAddress);
    }
    
    struct BatchAgreementResult {
        bool success;
        string errorMessage;
    }

    struct BatchVerificationResult {
        string agreementId;
        string purposeId;
        bool isValid;
    }

    // Batch create multiple agreements
    function batchCreateAgreements(
        string[] memory ids,
        address[] memory subjects,
        address[] memory processors,
        ConsentRegistry.Purpose[][] memory purposes,
        uint256[] memory validFroms,
        uint256[] memory validUntils,
        string[] memory metadataHashes
    ) public returns (BatchAgreementResult[] memory) {
        require(
            ids.length == subjects.length &&
            ids.length == processors.length &&
            ids.length == purposes.length &&
            ids.length == validFroms.length &&
            ids.length == validUntils.length &&
            ids.length == metadataHashes.length,
            "Array lengths must match"
        );

        BatchAgreementResult[] memory results = new BatchAgreementResult[](ids.length);

        for (uint i = 0; i < ids.length; i++) {
            try registry.createAgreement(
                ids[i],
                subjects[i],
                processors[i],
                purposes[i],
                validFroms[i],
                validUntils[i],
                metadataHashes[i]
            ) returns (bool) {
                results[i] = BatchAgreementResult(true, "");
            } catch Error(string memory reason) {
                results[i] = BatchAgreementResult(false, reason);
            } catch {
                results[i] = BatchAgreementResult(false, "Unknown error");
            }
        }

        return results;
    }

    // Batch verify multiple consents
    function batchVerifyConsents(
        string[] memory agreementIds,
        string[] memory purposeIds,
        address[] memory processors
    ) public view returns (BatchVerificationResult[] memory) {
        require(
            agreementIds.length == purposeIds.length &&
            agreementIds.length == processors.length,
            "Array lengths must match"
        );

        BatchVerificationResult[] memory results = new BatchVerificationResult[](agreementIds.length);

        for (uint i = 0; i < agreementIds.length; i++) {
            bool isValid = verifier.verifyConsent(
                agreementIds[i],
                purposeIds[i],
                processors[i]
            );
            
            results[i] = BatchVerificationResult(
                agreementIds[i],
                purposeIds[i],
                isValid
            );
        }

        return results;
    }

    // Batch update agreement statuses
    function batchUpdateAgreements(
        string[] memory ids,
        string[] memory statuses,
        string[] memory proofIds,
        string[] memory timestampProofs
    ) public returns (BatchAgreementResult[] memory) {
        require(
            ids.length == statuses.length &&
            ids.length == proofIds.length &&
            ids.length == timestampProofs.length,
            "Array lengths must match"
        );

        BatchAgreementResult[] memory results = new BatchAgreementResult[](ids.length);

        for (uint i = 0; i < ids.length; i++) {
            try registry.updateAgreement(
                ids[i],
                statuses[i],
                proofIds[i],
                timestampProofs[i]
            ) returns (bool) {
                results[i] = BatchAgreementResult(true, "");
            } catch Error(string memory reason) {
                results[i] = BatchAgreementResult(false, reason);
            } catch {
                results[i] = BatchAgreementResult(false, "Unknown error");
            }
        }

        return results;
    }
}