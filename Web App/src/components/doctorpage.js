import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { uploadFileToIPFS, viewFile } from '../ipfs';
import userLogo from '../imgs/user_logo.png';
import '../App.css';

export const DoctorLogin = ({ contract }) => {
  const [doctorId, setDoctorId] = useState('');
  const [doctorUsername, setDoctorUsername] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const verifyDoctor = async (e) => {
    e.preventDefault();
    try {
      const doctor = await contract.doctors(doctorId);
      
      if (doctor.isRegistered) {
        navigate(`/doctor-dashboard/${doctorId}`);
      } else {
        setError('Invalid doctor ID');
      }
    } catch (err) {
      setError('Error verifying doctor');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="flex flex-col items-center justify-center p-6 bg-white rounded shadow-md space-y-4">

        <h1 className='text-2xl'> Doctor Login Page </h1>

        <img src={userLogo} alt="Login Illustration" className="w-50 h-60 mb-4 py-3"/>
        
        <form onSubmit={verifyDoctor} className="space-y-4">

          <input type="text" placeholder="Doctor Username" value={doctorUsername}
            onChange={(e) => setDoctorUsername(e.target.value)}
            className="w-full p-2 border rounded"
          />

          <input type="text" placeholder="Wallet address" value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="w-full p-2 border rounded"
          />

          <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded">
            Login
          </button>
          {error && <p className="text-red-500">{error}</p>}
        </form>

        <button onClick={() => navigate('/')} className="w-full mb-4 px-4 py-2 bg-gray-600 text-white rounded">
          Back to Login Page
        </button>

      </div>
    </div>
  );
};

export const DoctorDashboard = ({ doctorContract, patientContract, getSignedContracts }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [doctor, setDoctor] = useState();
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [file, setFile] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // get doctor info 
        const doctorInfo = await doctorContract.getDoctor(id);
        setDoctor(doctorInfo[0])

        const authorizedPatients = await doctorContract.getAuthorizedPatients(id);
        console.log('current address : ', id);
        
        const patientsData = await Promise.all(
          authorizedPatients.map(async (patientId) => {
            const patient = await patientContract.getPatient(patientId);
            const patientRecords = await patientContract.getActiveRecords(patientId);
            const doctorRecords = patientRecords.filter(record => record[6] === id);
            console.log('doctorRecords : ', doctorRecords);
            
            return { 
                id: patientId, 
                name: patient[0],
                records: doctorRecords
            };

            return null;
          })
        );
        
        setPatients(patientsData.filter(p => p !== null));
        // console.log('patients : ',patients);
        

      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, [doctorContract, patientContract, id]);


  const addRecord = async (e) => {
    e.preventDefault();

    // Ensure required fields are filled
    if (!selectedPatient) {
        alert("Please select a patient.");
        return;
    }
    if (!file) {
        alert("Please upload a file.");
        return;
    }
    if (!title.trim()) {
        alert("Please provide a title.");
        return;
    }

    try {
        // Upload file to IPFS
        const fileCID = await uploadFileToIPFS(file);
        if (!fileCID) {
            throw new Error("Failed to upload file to IPFS.");
        }

        // Interact with the smart contract
        const { patientContract: signedDoctorContract } = await getSignedContracts();
        const tx = await signedDoctorContract.addMedicalRecord(
            selectedPatient.id,
            fileCID,
            'Unknown',
            file.name,
            title.trim(),
            description.trim(),
            ''
        );

        await tx.wait();

        // Fetch updated patient records
        const patientRecords = await signedDoctorContract.getActiveRecords(selectedPatient.id);
        const doctorRecords = patientRecords.filter(record => record.doctor === id);

        // Update state
        setPatients(patients.map(p =>
            p.id === selectedPatient.id ? { ...p, records: doctorRecords } : p
        ));

        // Reset fields
        setFile(null);
        setTitle('');
        setDescription('');
        alert('Record added successfully');
    } catch (err) {
        console.error("Error adding record:", err);
        alert('Error adding record: ' + err.message);
    }
  };


  return (
    <div className="p-6 max-w-4xl mx-auto">

      <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
        Back to Home
      </button>

      <h1 className="text-2xl mb-6">Doctor Dashboard: {doctor}</h1>
      <h4 className="text-l">Doctor Wallet : {id}</h4>
      <div className="mb-8">
        <h2 className="text-xl mb-4">Your Patients</h2>
        <div className="grid grid-cols-1 gap-4">
          {patients.map(patient => (
            <div key={patient.id}>
              <div 
                className={`p-4 border rounded cursor-pointer ${
                  selectedPatient?.id === patient.id ? 'border-blue-500' : ''
                }`}
                onClick={() => setSelectedPatient(patient)}
              >
                <p className="font-medium">Patient Name : {patient.name}</p>
              </div>
              
              {selectedPatient?.id === patient.id && (
                <div className="mt-4 ml-4">
                    <h3 className="text-lg mb-2">Previous Records</h3>
                    <div className="space-y-2">
                      {patient.records.map((record, idx) => (
                          <div key={idx} className="p-3 bg-gray-50 rounded">
                              <div className="flex justify-between text-sm text-gray-600">
                                  <span>file title: {record[3]} | file name: {record[2]} | {new Date(Number(record.timestamp) * 1000).toLocaleString()} </span>
                                  <button onClick={() => viewFile(record[0])} 
                                      className="text-blue-600 hover:underline"
                                  >
                                      View File
                                  </button>
                              </div>
                              {record[4] && (
                                <div className="mt-2 text-sm text-gray-800">
                                  <strong>Description:</strong> {record[4]}
                                </div>
                              )}
                              <div id={`folder-content-${record[0]}`} className="mt-2"></div> 
                          </div>
                      ))}
                      {patient.records.length === 0 && (
                          <p className="text-gray-500">No records yet</p>
                      )}
                  </div>
                </div>
            )}
            </div>
          ))}
          {patients.length === 0 && (
            <p className="text-gray-500">No patients have granted you access yet</p>
          )}
        </div>
      </div>
      
      {selectedPatient && (
      <div>
        <h2 className="text-xl mb-4">Add Record for {selectedPatient.name}</h2>
        <form onSubmit={addRecord} className="space-y-4">
            <input
                type="text"
                placeholder="Record Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full p-2 border rounded"
                required
            />
            <input
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                className="w-full p-2 border rounded"
                required
            />
            <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description"
                className="w-full p-2 border rounded"
                rows="4"
            />
            <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded"
            >
                Add Record
            </button>
        </form>
    </div>
    )}


    </div>
  );  
};