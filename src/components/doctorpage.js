import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export const DoctorLogin = ({ contract }) => {
  const [doctorId, setDoctorId] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const verifyDoctor = async (e) => {
    e.preventDefault();
    try {
      const doctor = await contract.doctors(doctorId);
      if (doctor.exists) {
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
      <div className="p-6 bg-white rounded shadow-md space-y-4">
        <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
          Back to Home
        </button>
        <form onSubmit={verifyDoctor} className="space-y-4">
          <h2 className="text-xl">Doctor Login</h2>
          <input
            type="text"
            placeholder="Doctor ID"
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="w-full p-2 border rounded"
          />
          <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded">
            Login
          </button>
          {error && <p className="text-red-500">{error}</p>}
        </form>
      </div>
    </div>
  );
};

export const DoctorDashboard = ({ doctorContract, patientContract, getSignedContracts }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const authorizedPatients = await doctorContract.getAuthorizedPatients(id);
        const patientsData = await Promise.all(
          authorizedPatients.map(async (patientId) => {
            const patient = await patientContract.patients(patientId);
            if (patient.exists) {
              const patientRecords = await doctorContract.getPatientRecords(patientId);
              const doctorRecords = patientRecords.filter(record => record.doctorId === id);
              return { 
                id: patientId, 
                name: patient.name,
                records: doctorRecords
              };
            }
            return null;
          })
        );
        setPatients(patientsData.filter(p => p !== null));
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, [doctorContract, patientContract, id]);

  const addRecord = async (e) => {
    e.preventDefault();
    if (!selectedPatient || !message) return;

    try {
      const { doctorContract: signedDoctorContract } = await getSignedContracts();
      const tx = await signedDoctorContract.addRecord(id, selectedPatient.id, message);
      await tx.wait();
      
      // Update records after adding new one
      const patientRecords = await doctorContract.getPatientRecords(selectedPatient.id);
      const doctorRecords = patientRecords.filter(record => record.doctorId === id);
      setPatients(patients.map(p => 
        p.id === selectedPatient.id ? { ...p, records: doctorRecords } : p
      ));
      
      setMessage('');
      alert('Record added successfully');
    } catch (err) {
      alert('Error adding record: ' + err.message);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
        Back to Home
      </button>
      <h1 className="text-2xl mb-6">Doctor Dashboard: {id}</h1>
      
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
                <p className="font-medium">{patient.name}</p>
                <p className="text-sm text-gray-600">ID: {patient.id}</p>
              </div>
              
              {selectedPatient?.id === patient.id && (
                <div className="mt-4 ml-4">
                  <h3 className="text-lg mb-2">Previous Records</h3>
                  <div className="space-y-2">
                    {patient.records.map((record, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded">
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>{new Date(Number(record.timestamp) * 1000).toLocaleString()}</span>
                        </div>
                        <p className="mt-1">{record.message}</p>
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
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full p-2 border rounded"
              rows="4"
              placeholder="Enter medical record..."
            />
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
              Add Record
            </button>
          </form>
        </div>
      )}
    </div>
  );
};