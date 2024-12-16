// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PatientManagement {
    address public admin;

    struct MedicalRecord {
        string ipfsHash;
        string fileType;
        string fileName;
        string title;
        string resume;
        uint256 timestamp;
        address doctor;
        bool isActive; 
        string previousVersion;
    }

    struct Patient {
        string username;
        string role;
        bool isRegistered;
    }

    mapping(address => Patient) public patients;
    mapping(address => MedicalRecord[]) public patientRecords;
    mapping(string => uint256) private recordIndexes; // Maps IPFS hash to array index

    event PatientRegistered(address indexed patientAddress, string username, string role);
    event MedicalRecordAdded(address indexed patientAddress, address indexed doctorAddress, string ipfsHash, uint256 timestamp);
    event MedicalRecordUpdated(address indexed patientAddress, string oldIpfsHash, string newIpfsHash, uint256 timestamp);

    constructor() {
        admin = msg.sender;
        patients[msg.sender] = Patient("admin", "admin", true);
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    function registerPatient(address _patientAddress, string memory _username, string memory _role) public onlyAdmin {
        require(!patients[_patientAddress].isRegistered, "Patient already registered");
        patients[_patientAddress] = Patient(_username, _role, true);
        emit PatientRegistered(_patientAddress, _username, _role);
    }

    function getPatient(address _patientAddress) public view returns (string memory username, string memory role) {
        require(patients[_patientAddress].isRegistered, "Patient not registered");
        Patient memory patient = patients[_patientAddress];
        return (patient.username, patient.role);
    }

    // , bool memory isRegistered
    // , patient.isRegistered

    function addMedicalRecord(
        address _patientAddress, 
        string memory _ipfsHash,
        string memory _fileType,
        string memory _fileName,
        string memory _title,
        string memory _resume,
        string memory _previousVersion
    ) external {
        require(patients[_patientAddress].isRegistered, "Patient not registered");
        
        // If updating an existing record
        if (bytes(_previousVersion).length > 0) {
            // Mark the old version as inactive
            uint256 oldIndex = recordIndexes[_previousVersion];
            patientRecords[_patientAddress][oldIndex].isActive = false;
            
            emit MedicalRecordUpdated(_patientAddress, _previousVersion, _ipfsHash, block.timestamp);
        }

        // Add new record
        MedicalRecord memory newRecord = MedicalRecord(
            _ipfsHash,
            _fileType,
            _fileName,
            _title,
            _resume,
            block.timestamp,
            msg.sender,
            true, 
            _previousVersion
        );

        patientRecords[_patientAddress].push(newRecord);
        recordIndexes[_ipfsHash] = patientRecords[_patientAddress].length - 1;
        
        emit MedicalRecordAdded(_patientAddress, msg.sender, _ipfsHash, block.timestamp);
    }

    function getMedicalRecords(address _patientAddress) public view returns (MedicalRecord[] memory) {
        require(patients[_patientAddress].isRegistered, "Patient not registered");
        return patientRecords[_patientAddress];
    }

    // New function to get only active records
    function getActiveRecords(address _patientAddress) public view returns (MedicalRecord[] memory) {
        require(patients[_patientAddress].isRegistered, "Patient not registered");
        
        // First, count active records
        uint256 activeCount = 0;
        for (uint256 i = 0; i < patientRecords[_patientAddress].length; i++) {
            if (patientRecords[_patientAddress][i].isActive) {
                activeCount++;
            }
        }
        
        // Create array of active records
        MedicalRecord[] memory activeRecords = new MedicalRecord[](activeCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 0; i < patientRecords[_patientAddress].length; i++) {
            if (patientRecords[_patientAddress][i].isActive) {
                activeRecords[currentIndex] = patientRecords[_patientAddress][i];
                currentIndex++;
            }
        }
        
        return activeRecords;
    }
}