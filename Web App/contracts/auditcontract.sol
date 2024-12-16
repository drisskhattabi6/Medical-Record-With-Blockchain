// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract HealthcareAudit {
    address public admin;
    
    struct AuditRecord {
        address actor;          // Who performed the action
        string actionType;      // Type of action (e.g., "RECORD_ADDED", "ACCESS_GRANTED")
        address subject;        // Who the action was performed on
        string details;         // Additional details
        uint256 timestamp;      // When the action occurred
    }
    
    AuditRecord[] public auditTrail;
    
    event AuditLogAdded(
        address indexed actor,
        string actionType,
        address indexed subject,
        string details,
        uint256 timestamp
    );
    
    constructor() {
        admin = msg.sender;
    }
    
    // Action types
    string public constant DOCTOR_REGISTERED = "DOCTOR_REGISTERED";
    string public constant PATIENT_REGISTERED = "PATIENT_REGISTERED";
    string public constant RECORD_ADDED = "RECORD_ADDED";
    string public constant ACCESS_GRANTED = "ACCESS_GRANTED";
    
    function addAuditLog(
        address _actor,
        string memory _actionType,
        address _subject,
        string memory _details
    ) external {
        AuditRecord memory newRecord = AuditRecord(
            _actor,
            _actionType,
            _subject,
            _details,
            block.timestamp
        );
        
        auditTrail.push(newRecord);
        
        emit AuditLogAdded(
            _actor,
            _actionType,
            _subject,
            _details,
            block.timestamp
        );
    }
    
    function getAuditTrail() public view returns (AuditRecord[] memory) {
        return auditTrail;
    }
    
    function getAuditTrailByActor(address _actor) public view returns (AuditRecord[] memory) {
        uint count = 0;
        for (uint i = 0; i < auditTrail.length; i++) {
            if (auditTrail[i].actor == _actor) {
                count++;
            }
        }
        
        AuditRecord[] memory result = new AuditRecord[](count);
        uint currentIndex = 0;
        
        for (uint i = 0; i < auditTrail.length; i++) {
            if (auditTrail[i].actor == _actor) {
                result[currentIndex] = auditTrail[i];
                currentIndex++;
            }
        }
        
        return result;
    }
    
    function getAuditTrailBySubject(address _subject) public view returns (AuditRecord[] memory) {
        uint count = 0;
        for (uint i = 0; i < auditTrail.length; i++) {
            if (auditTrail[i].subject == _subject) {
                count++;
            }
        }
        
        AuditRecord[] memory result = new AuditRecord[](count);
        uint currentIndex = 0;
        
        for (uint i = 0; i < auditTrail.length; i++) {
            if (auditTrail[i].subject == _subject) {
                result[currentIndex] = auditTrail[i];
                currentIndex++;
            }
        }
        
        return result;
    }
}