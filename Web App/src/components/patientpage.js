import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { viewFile } from '../ipfs';
import userLogo from '../imgs/user_logo.png';
import '../App.css';

export const PatientLogin = ({ contract }) => {
  const [patientId, setPatientId] = useState('');
  const [patientUsername, setPatientUsername] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const verifyPatient = async (e) => {
    e.preventDefault();
    try {
      const patient = await contract.patients(patientId);
      if (patient.isRegistered) {
        navigate(`/patient-dashboard/${patientId}`);
      } else {
        setError('Invalid patient ID');
      }
    } catch (err) {
      setError('Error verifying patient');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="flex flex-col items-center justify-center p-6 bg-white rounded shadow-md space-y-4">
    
            <h1 className='text-2xl'> Patient Login Page </h1>
    
            <img src={userLogo} alt="Login Illustration" className="w-50 h-60 mb-4 py-3"/>
            
            <form onSubmit={verifyPatient} className="space-y-4">
    
              <input type="text" placeholder="Patient Username" value={patientUsername}
                onChange={(e) => setPatientUsername(e.target.value)}
                className="w-full p-2 border rounded"
              />
    
              <input type="text" placeholder="Wallet address" value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
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


export const PatientDashboard = ({ doctorContract, patientContract, getSignedContracts }) => {
  const { id } = useParams(); // Patient address
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState([]);
  const [records, setRecords] = useState([]);
  const [patient, setPatient] = useState();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // get patient data
        const patientInfo = await patientContract.getPatient(id);
        const patientDetails = {
          username: patientInfo[0],
          role: patientInfo[1],
        };
        setPatient(patientDetails);

        // get doctors data
        const doctorIds = await doctorContract.getAllDoctors();
        const doctorsData = await Promise.all(
          doctorIds.map(async (doctorId) => {
            const doctor = await doctorContract.getDoctor(doctorId);

            if (doctor[1] === 'admin') return null; 

            const hasAccess = await doctorContract.isAuthorized(doctorId, id);
            return { id: doctorId, name: doctor[0], hasAccess };
          })
        );
        const feltreddoctorsData = doctorsData.filter((data) => data !== null);
        setDoctors(feltreddoctorsData);

        // get recors data
        const allRecords = await patientContract.getActiveRecords(id);
        const recordData = await Promise.all(
          allRecords.map(async (record) => {
            const doctor = await doctorContract.getDoctor(record[6]);

            if (doctor[1] === 'admin') return null; 

            // const hasAccess = await doctorContract.isAuthorized(record[6], id);
            // if (!hasAccess) return null;

            return { 
              recordCDI: record[0], 
              fileName: record[2], 
              title: record[3], 
              description: record[4], 
              datetime: record[5], 
              doctor: doctor
            };
          })
        )
        const feltredrecordData = recordData.filter((data) => data !== null);
        setRecords(feltredrecordData);
        // console.log('records :\n',feltredrecordData);
        
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, [doctorContract, patientContract, id, doctors]);

  const grantAccess = async (doctorId) => {
    try {
      const { doctorContract: signedDoctorContract, patientContract: signedPatientContract } = 
        await getSignedContracts();
      
      const tx2 = await signedDoctorContract.addPatientAccess(doctorId, id);
      await tx2.wait();

      
      setDoctors(doctors.map(d => 
        d.id === doctorId ? { ...d, hasAccess: true } : d
      ));

    } catch (err) {
      alert('Error granting access: ' + err.message);
    }
  };

  const revokeAccess = async (doctorId) => {
    try {
      const { doctorContract: signedDoctorContract, patientContract: signedPatientContract } = 
        await getSignedContracts();
      
      const tx2 = await signedDoctorContract.revokePatientAccess(doctorId, id)
      await tx2.wait();

      
      setDoctors(doctors.map(d => 
        d.id === doctorId ? { ...d, hasAccess: false } : d
      ));

    } catch (err) {
      alert('Error granting access: ' + err.message);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
        Back to Home
      </button>

      <h1 className="text-2xl mb-6">Patient Dashboard:</h1>

      {patient ? (
        <div className="mb-4">
          <h2 className="text-xl font-bold">Patient Information</h2>
          <p><strong>Name:</strong> {patient.username}</p>
          <p><strong>Wallet Address:</strong> {id}</p>
        </div>
      ) : (
        <p>Loading patient information...</p>
      )}
      
      <div className="mb-8">
        <h2 className="text-xl mb-4">Available Doctors</h2>
        <div className="grid grid-cols-1 gap-4">
          {doctors.map(doctor => (
            <div key={doctor.id} className="p-4 border rounded flex justify-between items-center">
              <div>
                <p className="font-medium">{doctor.name}</p>
              </div>
              {!doctor.hasAccess && (
                <button 
                  onClick={() => grantAccess(doctor.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded"
                > Grant Access
                </button>
              )}
              {doctor.hasAccess && (
                // <span className="text-green-600">Access Granted</span>
                <button 
                onClick={() => revokeAccess(doctor.id)} 
                className="px-4 py-2 bg-red-600 text-white rounded">
                   Revoke Access 
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <h2 className="text-xl mb-4">Medical Records</h2>
        <div className="space-y-4">
          {records.map((record, index) => (
            <div key={index} className="p-4 border rounded">
              <div className="flex justify-between items-center mb-2">
                <p className="font-medium">Title : {record.title} | From Dr.{record.doctor[0]}</p>
                <p className="text-sm text-gray-600">
                {record.fileName} | {new Date(Number(record.datetime) * 1000).toLocaleString()}
                </p>
                <button 
                  onClick={() => viewFile(record.recordCDI)} 
                  className="px-4 py-2 bg-blue-600 text-white rounded"
                >
                  View File
                </button>
              </div>
              {record.description && (
                <div className="mt-2 text-sm text-gray-800">
                  <strong>Description:</strong> {record.description}
                </div>
              )}
              <div id={`folder-content-${record.recordCDI}`} className="mt-2"></div> 
            </div>
          ))}
          {records.length === 0 && (
            <p className="text-gray-500">No medical records available</p>
          )}
        </div>
      </div>
    </div>
  );
};
