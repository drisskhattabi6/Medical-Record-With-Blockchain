import React, { useState, useEffect } from 'react';
import { BrowserProvider, Contract } from 'ethers';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Admin from './components/adminpage';
import { DoctorLogin, DoctorDashboard } from './components/doctorpage';
import { PatientLogin, PatientDashboard } from './components/patientpage';

const doctorContractABI = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "wallet",
				"type": "address"
			}
		],
		"name": "DoctorRegistered",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "message",
				"type": "string"
			}
		],
		"name": "RecordAdded",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			}
		],
		"name": "addPatientAccess",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "message",
				"type": "string"
			}
		],
		"name": "addRecord",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "doctorIds",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "doctors",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "wallet",
				"type": "address"
			},
			{
				"internalType": "bool",
				"name": "exists",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getAllDoctors",
		"outputs": [
			{
				"internalType": "string[]",
				"name": "",
				"type": "string[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			}
		],
		"name": "getAuthorizedPatients",
		"outputs": [
			{
				"internalType": "string[]",
				"name": "",
				"type": "string[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			}
		],
		"name": "getPatientRecords",
		"outputs": [
			{
				"components": [
					{
						"internalType": "string",
						"name": "message",
						"type": "string"
					},
					{
						"internalType": "uint256",
						"name": "timestamp",
						"type": "uint256"
					},
					{
						"internalType": "string",
						"name": "doctorId",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "doctorName",
						"type": "string"
					}
				],
				"internalType": "struct DoctorManagement.Record[]",
				"name": "",
				"type": "tuple[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "patientRecords",
		"outputs": [
			{
				"internalType": "string",
				"name": "message",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "doctorName",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			}
		],
		"name": "registerDoctor",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
];

const patientContractABI = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			}
		],
		"name": "AccessGranted",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "wallet",
				"type": "address"
			}
		],
		"name": "PatientRegistered",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			}
		],
		"name": "grantAccessToDoctor",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			}
		],
		"name": "hasDoctorAccess",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "patients",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "wallet",
				"type": "address"
			},
			{
				"internalType": "bool",
				"name": "exists",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			}
		],
		"name": "registerPatient",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
];

const doctorContractAddress = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
const patientContractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";


const Home = ({ doctorContract, patientContract, account, connectWallet }) => {
	const [error, setError] = useState('');
	const navigate = useNavigate();
  
	const connectAsAdmin = async () => {
	  try {
		await connectWallet();
		const doctorOwner = await doctorContract.owner();
		const patientOwner = await patientContract.owner();
		
		if (!account || doctorOwner.toLowerCase() !== account.toLowerCase() || 
			patientOwner.toLowerCase() !== account.toLowerCase()) {
		  setError('Not authorized as admin');
		  return;
		}
		navigate('/admin');
	  } catch (err) {
		setError('Error verifying admin');
	  }
	};
  
	return (
	  <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
		<div className="space-y-4">
		  <button onClick={connectAsAdmin} className="w-full px-6 py-3 bg-blue-600 text-white rounded">
			Connect as Admin
		  </button>
		  <button onClick={() => navigate('/doctor-login')} className="w-full px-6 py-3 bg-green-600 text-white rounded">
			Connect as Doctor
		  </button>
		  <button onClick={() => navigate('/patient-login')} className="w-full px-6 py-3 bg-purple-600 text-white rounded">
			Connect as Patient
		  </button>
		  {error && <p className="text-red-500">{error}</p>}
		</div>
	  </div>
	);
  };
  
  const App = () => {
	const [doctorContract, setDoctorContract] = useState(null);
	const [patientContract, setPatientContract] = useState(null);
	const [account, setAccount] = useState('');
	const [provider, setProvider] = useState(null);
	const [signer, setSigner] = useState(null);
  
	const connectWallet = async () => {
	  if (!window.ethereum) return;
	  try {
		const accounts = await window.ethereum.request({
		  method: 'eth_requestAccounts'
		});
		setAccount(accounts[0]);
		const newSigner = await provider.getSigner();
		setSigner(newSigner);
	  } catch (err) {
		console.error("Error connecting wallet:", err);
	  }
	};
  
	useEffect(() => {
	  const init = async () => {
		if (window.ethereum) {
		  const provider = new BrowserProvider(window.ethereum);
		  setProvider(provider);
		  
		  const doctorContract = new Contract(doctorContractAddress, doctorContractABI, provider);
		  const patientContract = new Contract(patientContractAddress, patientContractABI, provider);
		  
		  setDoctorContract(doctorContract);
		  setPatientContract(patientContract);
  
		  window.ethereum.on('accountsChanged', async (accounts) => {
			setAccount(accounts[0] || '');
			if (accounts[0]) {
			  const newSigner = await provider.getSigner();
			  setSigner(newSigner);
			} else {
			  setSigner(null);
			}
		  });
		}
	  };
  
	  init();
	}, []);
  
	const getSignedContracts = async () => {
	  if (!signer) {
		const newSigner = await provider.getSigner();
		setSigner(newSigner);
		return {
		  doctorContract: doctorContract.connect(newSigner),
		  patientContract: patientContract.connect(newSigner)
		};
	  }
	  return {
		doctorContract: doctorContract.connect(signer),
		patientContract: patientContract.connect(signer)
	  };
	};
  
	if (!doctorContract || !patientContract) return <div>Loading...</div>;
  
	return (
	  <BrowserRouter>
		<Routes>
		  <Route path="/" element={
			<Home 
			  doctorContract={doctorContract} 
			  patientContract={patientContract} 
			  account={account}
			  connectWallet={connectWallet}
			/>
		  } />
		  <Route path="/admin" element={
			<Admin getSignedContracts={getSignedContracts} />
		  } />
		  <Route path="/doctor-login" element={
			<DoctorLogin contract={doctorContract} />
		  } />
		  <Route path="/doctor-dashboard/:id" element={
  <DoctorDashboard 
    doctorContract={doctorContract}
    patientContract={patientContract}
    getSignedContracts={getSignedContracts}
  />
} />
		  <Route path="/patient-login" element={
			<PatientLogin contract={patientContract} />
		  } />
		  <Route path="/patient-dashboard/:id" element={
  <PatientDashboard 
    doctorContract={doctorContract}
    patientContract={patientContract}
    getSignedContracts={getSignedContracts}
  />
} />
		  <Route path="*" element={<Navigate to="/" />} />
		</Routes>
	  </BrowserRouter>
	);
  };
  
  export default App;  