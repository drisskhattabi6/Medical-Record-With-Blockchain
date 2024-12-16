import { create } from 'ipfs-http-client';

const ipfsClient = create({ url: 'http://localhost:5001/api/v0' });


export const uploadFileToIPFS = async (file) => {
    try {
        // console.log('uploadFileToIPFS');
        
        // Upload the file to IPFS
        const added = await ipfsClient.add({
            path: file.name,
            content: file,
        });

        // Log and return the file CID
        console.log(`File uploaded successfully! CID: ${added.cid.toString()}`);
        return added.cid.toString();
    } catch (error) {
        console.error("Error uploading file to IPFS:", error);
        throw error;
    }
};

export const viewFile = async (fileCID) => {
    try {
        // Construct the file URL
        const fileUrl = `http://127.0.0.1:8080/ipfs/${fileCID}`;
        console.log(`Opening file from ${fileUrl}`);
        
        // Fetch the file to check if it exists and is accessible
        const response = await fetch(fileUrl);
        if (!response.ok) throw new Error(`Failed to fetch file: ${response.statusText}`);
        
        // Open the file in the default browser (new tab)
        window.open(fileUrl, '_blank');
    } catch (error) {
        console.error('Error viewing file:', error);
        alert(`Error: ${error.message}`);
    }
};
