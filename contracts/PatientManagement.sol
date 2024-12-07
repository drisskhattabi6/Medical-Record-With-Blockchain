// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PatientManagement {
    address public owner;
    
    struct Patient {
        string name;
        address wallet;
        bool exists;
        mapping(string => bool) doctorAccess;
    }
    
    mapping(string => Patient) public patients;
    
    event PatientRegistered(string patientId, string name, address wallet);
    event AccessGranted(string patientId, string doctorId);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function registerPatient(string memory patientId, string memory name) public onlyOwner {
        require(!patients[patientId].exists, "Patient ID already exists");
        patients[patientId].name = name;
        patients[patientId].wallet = tx.origin; // Changed from msg.sender
        patients[patientId].exists = true;
        emit PatientRegistered(patientId, name, tx.origin);
    }
    
    function grantAccessToDoctor(string memory patientId, string memory doctorId) public {
        require(patients[patientId].exists, "Patient does not exist");
        patients[patientId].doctorAccess[doctorId] = true;
        emit AccessGranted(patientId, doctorId);
    }
    
    function hasDoctorAccess(string memory patientId, string memory doctorId) public view returns (bool) {
        require(patients[patientId].exists, "Patient does not exist");
        return patients[patientId].doctorAccess[doctorId];
    }

    function getPatient(string memory patientId) 
        public 
        view 
        returns (string memory name, address wallet, bool exists) 
    {
        require(patients[patientId].exists, "Patient does not exist");
        Patient storage patient = patients[patientId];
        return (patient.name, patient.wallet, patient.exists);
    }

}