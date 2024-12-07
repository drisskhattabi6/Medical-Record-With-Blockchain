import { create } from 'ipfs-http-client';
import sha256 from 'js-sha256';

const ipfsClient = create({ url: 'http://localhost:5001/api/v0' });


export const uploadFilesToIPFS = async (files, doctorId, patientId) => {
    try {

        const doctorFolder = sha256(doctorId); 
        const patientFolder = sha256(patientId);

        const folderHash = sha256(doctorFolder + patientFolder); 

        // Add files with paths reflecting the folder hierarchy
        const filesWithPaths = files.map((file, index) => ({
            path: `${folderHash}/file_${index}_${file.name}`,
            content: file,
        }));

        // Upload files to IPFS with the folder path
        const added = await ipfsClient.addAll(filesWithPaths, { wrapWithDirectory: true });

        let folderCID = null;
        // Extract the CID for the folder
        for await (const item of added) {
            if (item.path === folderHash) {
                folderCID = item.cid.toString(); // Get the folder's CID
            }
        }

        if (!folderCID) {
            throw new Error("Failed to create or locate folder CID");
        }

        console.log(`Folder CID: ${folderCID}`);
        return folderCID;
    } catch (error) {
        console.error("Error uploading files to IPFS:", error);
        throw error;
    }
};


const restructureHTML = (htmlString) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, 'text/html');

    const grid = doc.querySelector('.grid.dir');
    const allDivs = Array.from(grid.children);

    const newGrid = document.createElement('div');
    newGrid.className = 'grid dir';

    for (let i = 0; i < allDivs.length; i += 4) {
        const row = document.createElement('div');
        row.className = 'file-row';
        // row.appendChild(allDivs[i]);     // type-icon div
        row.appendChild(allDivs[i + 1]); // file name div
        row.appendChild(allDivs[i + 2]); // hash link div
        row.appendChild(allDivs[i + 3]); // size div
        newGrid.appendChild(row);
    }

    // console.log('Restructured HTML:', newGrid.outerHTML);
    return newGrid.outerHTML;
  };


export  const viewFolder = async (folderCID) => {
    try {
        console.log(`folderCID : ${folderCID}`);
        const fileUrl = `http://127.0.0.1:8080/ipfs/${folderCID}`;
        console.log(`Fetching folder from ${fileUrl}`);
          
        const response = await fetch(fileUrl);
          if (!response.ok) throw new Error(`Failed to fetch content: ${response.statusText}`);

          const text = await response.text();

          const parser = new DOMParser();
          const doc = parser.parseFromString(text, 'text/html');

          let folderSection = doc.querySelector('section');

          const links = folderSection.querySelectorAll('a');
              links.forEach(link => {
                  if (link.getAttribute('href').startsWith('/ipfs/')) {
                      const relativePath = link.getAttribute('href');
                      link.setAttribute('href', `http://127.0.0.1:8080${relativePath}`);
                      link.setAttribute('target', '_blank');
                  }
              });

          if (folderSection) {
              folderSection = restructureHTML(folderSection.outerHTML);

              const container = document.querySelector(`#folder-content-${folderCID}`);
              if (container) {
                  container.innerHTML = folderSection;
              } else {
                  console.error('Container not found for displaying folder content.');
              }
          } else {
              console.error('Folder section not found in the fetched content.');
          }
    } catch (error) {
          console.error('Error viewing folder:', error);
          alert(`Error: ${error.message}`);
    }
};


//   // Function to get folder content from IPFS
// export const getFolderContent = async (cid) => {
//     try {

//       const result = await ipfsClient.get(cid);

//       if (Array.isArray(result)) {

//         return result.map((file) => ({
//           path: file.path,
//           cid: file.cid.toString(),
//           size: file.size,
//         }));

//       } else {
//         console.log('Expected an array, but got:', result);
//         return [];
//       }

//     } catch (error) {
//       console.error("Error getting folder content from IPFS:", error);
//       throw error;
//     }
// };
  