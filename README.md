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
    - can add patient
    - can edit the medical folder of their patients

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

---

### Example of Editing a File in a Folder:
Below is an updated function for editing a file in a folder:

```javascript
export const editFileInFolder = async (folderCID, newFile, filePath) => {
    try {
        // Retrieve existing files in the folder
        const existingFiles = await getFolderContent(folderCID);

        // Find the file that matches the filePath and replace it with the new file
        const updatedFiles = existingFiles.filter(file => file.path !== filePath); // Remove the old file
        updatedFiles.push({
            path: filePath,   // New file path in the folder
            content: newFile, // New file content
        });

        // Re-upload the folder with the new file
        const added = await ipfsClient.addAll(updatedFiles, { wrapWithDirectory: true });
        let newFolderCID = null;

        // Extract the CID for the updated folder
        for await (const item of added) {
            if (item.path === folderCID) {
                newFolderCID = item.cid.toString();
            }
        }

        if (!newFolderCID) {
            throw new Error("Failed to upload updated folder CID");
        }

        console.log(`Updated Folder CID: ${newFolderCID}`);
        return newFolderCID; // Return the new CID for the updated folder
    } catch (error) {
        console.error("Error editing file in folder:", error);
        throw error;
    }
};
```

---

### Example of Deleting a File from a Folder:
Below is an updated function for deleting a file from a folder:

```javascript
export const deleteFileFromFolder = async (folderCID, filePathToDelete) => {
    try {
        // Retrieve existing files in the folder
        const existingFiles = await getFolderContent(folderCID);

        // Remove the file you want to delete
        const updatedFiles = existingFiles.filter(file => file.path !== filePathToDelete);

        // Re-upload the folder with the file removed
        const added = await ipfsClient.addAll(updatedFiles, { wrapWithDirectory: true });
        let newFolderCID = null;

        // Extract the CID for the updated folder
        for await (const item of added) {
            if (item.path === folderCID) {
                newFolderCID = item.cid.toString();
            }
        }

        if (!newFolderCID) {
            throw new Error("Failed to upload updated folder CID");
        }

        console.log(`Updated Folder CID: ${newFolderCID}`);
        return newFolderCID; // Return the new CID for the updated folder
    } catch (error) {
        console.error("Error deleting file from folder:", error);
        throw error;
    }
};
```

---

### Key Points:
1. **Immutable File System:**
   - IPFS is immutable, meaning once data is added, it cannot be changed. Instead, you must create a new CID for any modifications.

2. **Re-uploading Folders:**
   - When editing or deleting a file, you re-upload the whole folder (with the updated content), and IPFS will generate a new CID for the folder.

3. **Updating the CID in Your System:**
   - After re-uploading, update the CID stored in your system (e.g., the blockchain or database) to the new CID of the updated folder.

### Conclusion:
To edit or delete a file in IPFS, you will always end up creating a new folder CID, but the content (including your edited or deleted file) will be updated under the new CID. This process mimics the idea of modifying or deleting a file in a folder.

Let me know if you need more details or help with specific parts!