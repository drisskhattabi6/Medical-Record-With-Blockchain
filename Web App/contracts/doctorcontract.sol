// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DoctorManagement {
    address public admin;

    struct Doctor {
        string username;
        string role;
        bool isRegistered;
    }

    mapping(address => Doctor) public doctors;
    address[] private doctorAddresses;
    mapping(address => address[]) public doctorPatients;
    mapping(address => mapping(address => bool)) public doctorPatientAccess; // Maps doctor to patient access status

    event DoctorRegistered(address indexed doctorAddress, string username, string role);
    event PatientAccessGranted(address indexed doctorAddress, address indexed patientAddress);
    event PatientAccessRevoked(address indexed doctorAddress, address indexed patientAddress);

    constructor() {
        admin = msg.sender;
        doctors[msg.sender] = Doctor("admin", "admin", true);
        doctorAddresses.push(msg.sender);
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    function registerDoctor(address _doctorAddress, string memory _username, string memory _role) public onlyAdmin {
        require(!doctors[_doctorAddress].isRegistered, "Doctor already registered");
        doctors[_doctorAddress] = Doctor(_username, _role, true);
        doctorAddresses.push(_doctorAddress);
        emit DoctorRegistered(_doctorAddress, _username, _role);
    }

    function addPatientAccess(address _doctorAddress, address _patientAddress) external {
        require(doctors[_doctorAddress].isRegistered, "Doctor not registered");
        require(!doctorPatientAccess[_doctorAddress][_patientAddress], "Access already granted");
        
        doctorPatients[_doctorAddress].push(_patientAddress);
        doctorPatientAccess[_doctorAddress][_patientAddress] = true;
        
        emit PatientAccessGranted(_doctorAddress, _patientAddress);
    }

    function revokePatientAccess(address _doctorAddress, address _patientAddress) external {
        require(doctors[_doctorAddress].isRegistered, "Doctor not registered");
        require(doctorPatientAccess[_doctorAddress][_patientAddress], "Access not granted");
        require(msg.sender == _patientAddress, "Only patient can revoke access");
        
        // Remove access
        doctorPatientAccess[_doctorAddress][_patientAddress] = false;
        
        // Remove from doctorPatients array
        address[] storage patients = doctorPatients[_doctorAddress];
        for (uint i = 0; i < patients.length; i++) {
            if (patients[i] == _patientAddress) {
                // Move the last element to the position being deleted
                patients[i] = patients[patients.length - 1];
                // Remove the last element
                patients.pop();
                break;
            }
        }
        
        emit PatientAccessRevoked(_doctorAddress, _patientAddress);
    }

    function getDoctor(address _doctorAddress) public view returns (string memory username, string memory role) {
        require(doctors[_doctorAddress].isRegistered, "Doctor not registered");
        Doctor memory doctor = doctors[_doctorAddress];
        return (doctor.username, doctor.role);
    }

    function getAuthorizedPatients(address _doctorAddress) public view returns (address[] memory) {
        return doctorPatients[_doctorAddress];
    }

    function isAuthorized(address _doctorAddress, address _patientAddress) public view returns (bool) {
        return doctorPatientAccess[_doctorAddress][_patientAddress];
    }

    function getAllDoctors() public view returns (address[] memory) {
        return doctorAddresses;
    }

}