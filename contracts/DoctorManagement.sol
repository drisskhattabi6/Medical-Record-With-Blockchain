// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DoctorManagement {
    address public owner;
    string[] public doctorIds;
    
    struct Doctor {
        string name;
        address wallet;
        bool exists;
        string[] patients;
    }
    
    struct Record {
        string message;
        uint256 timestamp;
        string doctorId;
        string doctorName;
    }
    
    mapping(string => Doctor) public doctors;
    mapping(string => mapping(string => Record[])) public patientRecords;
    
    event DoctorRegistered(string doctorId, string name, address wallet);
    event RecordAdded(string patientId, string doctorId, string message);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
function registerDoctor(string memory doctorId, string memory name) public onlyOwner {
    require(!doctors[doctorId].exists, "Doctor ID already exists");
    doctors[doctorId] = Doctor({
        name: name,
        wallet: tx.origin, // Changed from msg.sender
        exists: true,
        patients: new string[](0)
    });
    doctorIds.push(doctorId);
    emit DoctorRegistered(doctorId, name, tx.origin);
}


    function addPatientAccess(string memory doctorId, string memory patientId) public {
        require(doctors[doctorId].exists, "Doctor does not exist");
        doctors[doctorId].patients.push(patientId);
    }

    function getAuthorizedPatients(string memory doctorId) public view returns (string[] memory) {
        require(doctors[doctorId].exists, "Doctor does not exist");
        return doctors[doctorId].patients;
    }

    function getAllDoctors() public view returns (string[] memory) {
        return doctorIds;
    }
    
    function addRecord(string memory doctorId, string memory patientId, string memory message) public {
        require(doctors[doctorId].exists, "Doctor does not exist");
        bool hasAccess = false;
        string[] memory authorizedPatients = doctors[doctorId].patients;
        
        for(uint i = 0; i < authorizedPatients.length; i++) {
            if(keccak256(bytes(authorizedPatients[i])) == keccak256(bytes(patientId))) {
                hasAccess = true;
                break;
            }
        }
        require(hasAccess, "Doctor not authorized for this patient");
        
        Record memory newRecord = Record({
            message: message,
            timestamp: block.timestamp,
            doctorId: doctorId,
            doctorName: doctors[doctorId].name
        });
        
        patientRecords[doctorId][patientId].push(newRecord);
        emit RecordAdded(patientId, doctorId, message);
    }
    
    function getPatientRecords(string memory patientId) public view returns (Record[] memory) {
        uint totalRecords = 0;
        for(uint i = 0; i < doctorIds.length; i++) {
            totalRecords += patientRecords[doctorIds[i]][patientId].length;
        }
        
        Record[] memory allRecords = new Record[](totalRecords);
        uint currentIndex = 0;
        
        for(uint i = 0; i < doctorIds.length; i++) {
            Record[] memory doctorRecords = patientRecords[doctorIds[i]][patientId];
            for(uint j = 0; j < doctorRecords.length; j++) {
                allRecords[currentIndex] = doctorRecords[j];
                currentIndex++;
            }
        }
        
        return allRecords;
    }
}