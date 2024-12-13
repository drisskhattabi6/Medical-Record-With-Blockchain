### Overview of the Doctor Management Contract

This Solidity smart contract manages doctors, their access to patients, and records associated with those interactions. Here's what it does:

### **Core Features**

1. **Doctor Registration**
   - **What It Does:**  
     Allows the contract owner to register doctors with a unique ID, name, and wallet address.  
     - The doctor data includes their authorized patients and ensures each `doctorId` is unique.
   - **Functions:**
     - `registerDoctor`: Registers a doctor (only accessible by the owner).
   - **Events:**
     - `DoctorRegistered`: Emitted when a doctor is registered.


2. **Patient Access Control**
   - **What It Does:**  
     Manages the relationship between doctors and their patients. Doctors can only access records for patients they are authorized to treat.  
   - **Functions:**
     - `addPatientAccess`: Grants a doctor access to a specific patient.
     - `getAuthorizedPatients`: Returns a list of patients authorized for a doctor.
   - **Events:**
     - `PatientAccessAdded`: Emitted when a doctor gains access to a patient.

3. **Record Management**
   - **What It Does:**  
     Stores records associated with a patient and doctor. Each record contains a unique identifier (folder hash), timestamp, and references to both doctor and patient IDs.  
   - **Functions:**
     - `addRecord`: Adds a record for a doctor-patient pair. Ensures the doctor is authorized to access the patient before adding.
     - `getPatientRecords`: Retrieves all records for a patient across all doctors.
   - **Events:**
     - `RecordAdded`: Emitted when a record is created.


4. **Folder Hash Storage**
   - **What It Does:**  
     Allows any user to store and retrieve general-purpose folder hashes independently of the doctor-patient record system.  
   - **Functions:**
     - `addFolderHash`: Associates a folder hash with the caller’s wallet address.
     - `getUserFolders`: Retrieves all folder hashes linked to a specific address.


### **Use Cases**
1. **Registering a Doctor:**  
   The owner adds a new doctor, enabling them to interact with the system.
2. **Granting Patient Access:**  
   A doctor is given authorization to view and add records for a specific patient.
3. **Adding a Record:**  
   A doctor creates a record for an authorized patient, which is stored with a unique ID and timestamp.
4. **Retrieving Patient Records:**  
   All records for a specific patient can be retrieved across multiple doctors.
5. **Managing Folder Hashes:**  
   Users (e.g., doctors) can store unrelated folder hashes and retrieve them as needed.

----- 

### Overview of the Patient Management Contract

This Solidity smart contract manages patient data and controls access to their information by doctors. It ensures that only authorized doctors can access a specific patient's data.

---

### **Core Features**

1. **Patient Registration**
   - **What It Does:**  
     Allows the contract owner to register new patients with a unique ID, name, and wallet address.  
   - **Functionality:**
     - `registerPatient`: Adds a patient to the system (only the contract owner can call this).
   - **Events:**
     - `PatientRegistered`: Emitted when a new patient is registered.

---

2. **Access Control for Doctors**
   - **What It Does:**  
     Manages which doctors are allowed to access a patient's information.  
   - **Functionality:**
     - `grantAccessToDoctor`: Grants a specific doctor access to a patient's data.
     - `hasDoctorAccess`: Verifies if a doctor has been granted access to a specific patient.
   - **Events:**
     - `AccessGranted`: Emitted when a doctor is authorized to access a patient.


### **Use Cases**
1. **Registering a Patient:**
   - The owner registers a patient with a unique `patientId` and their personal details.
2. **Granting Doctor Access:**
   - Doctors can be granted access to specific patients by updating the `doctorAccess` mapping.
3. **Checking Doctor Authorization:**
   - Verifies whether a doctor has access to a specific patient using the `hasDoctorAccess` function.

