# blockchain-project

- you must first deploy the contracts first
- then get the ABI and the ID of each Contract
- in 'src/patientContractABI.json' and 'src/doctorContractABI.json' files put the ABI
- in scr/App.js put the ids of the contracts

```
const doctorContractAddress = "ContractAddress";
const patientContractAddress = "ContractAddress";
```

-------------

## Run IPFS in Docker
```
docker run -d --name ipfs_host -p 4001:4001 -p 5001:5001 -p 8080:8080 ipfs/kubo
```

- 4001: Peer-to-peer communication.
- 5001: API access.
- 8080: Gateway for accessing files.

### Then Install IPFS HTTP Client

Install the ipfs-http-client library in your React app:

```
npm install ipfs-http-client
```
----

### functionalities : 

- admin : 
    - autentificatien (the owner of the contract)
    - can add doctor or patient to the blockchain using it account

- doctor : 
    - autentificatien
    - can add patient (mazal mazidta)
    - can edit the medical folder of their patients (ymklo rir ichof l folder, mazal mazidt edit)
    7it maymknchi t editi wla t tmsa7 l folder mn IPFS

- patient :
    - autentificatien 
    - can only view his medical folder
    - can autorize the doctor 

---

### more informationes : 

- the medical folder will be stored in IPFS, and the name of this folder will be a hash code given by IPFS, this hash code with be stored in the blockchain.

---

# Getting Started with Create React App

In the project directory, you can run:

- `npm install` for the first time
- `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.


----

IPFS doesn't directly support modifying or deleting files once they've been uploaded because it is a content-addressed, immutable file system. This means that every change to the content of a file results in a new CID. However, you can "simulate" updating or deleting files by following these approaches:

### 1. **Editing a File:**
   To "edit" a file, you would need to:
   - Retrieve the original folder (CID).
   - Modify the file (e.g., edit the content).
   - Upload the modified file to IPFS as a new file.
   - Re-upload the entire folder structure (including the modified file) to IPFS, generating a new CID.
   - Replace the old CID with the new CID in your system (e.g., blockchain record).

### 2. **Deleting a File:**
   To "delete" a file, you would need to:
   - Retrieve the original folder (CID).
   - Remove the file from the local file system (before uploading).
   - Re-upload the remaining files to IPFS, generating a new CID.
   - Replace the old CID with the new CID in your system.

Since IPFS uses content addressing, both of these operations (editing or deleting) involve creating a new CID for the modified or new folder.

---

### Approach to Edit or Delete Files from Folder:

1. **Download the Current Folder's Files (if any):**
   - Retrieve the CID for the current folder.
   - Use `ipfs.cat` to fetch the content or `ipfs.ls` to list the files in the folder.

2. **Modify or Remove the File Locally:**
   - Modify the file on your local machine (e.g., edit the file or remove it).

3. **Re-upload the Folder (with New Content) to IPFS:**
   - After modification or deletion, re-upload the entire folder structure (including the modified or deleted file) to IPFS.
   - Get the new CID of the folder.

4. **Update the Folder's CID in Your Application (e.g., Blockchain):**
   - After the folder is re-uploaded and a new CID is generated, replace the old CID with the new one in your records.
