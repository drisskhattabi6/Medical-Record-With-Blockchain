import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export const PatientLogin = ({ contract }) => {
  const [patientId, setPatientId] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const verifyPatient = async (e) => {
    e.preventDefault();
    try {
      const patient = await contract.patients(patientId);
      if (patient.exists) {
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
      <div className="p-6 bg-white rounded shadow-md space-y-4">
        <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
          Back to Home
        </button>
        <form onSubmit={verifyPatient} className="space-y-4">
          <h2 className="text-xl">Patient Login</h2>
          <input
            type="text"
            placeholder="Patient ID"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
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

export const PatientDashboard = ({ doctorContract, patientContract, getSignedContracts }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState([]);
  const [records, setRecords] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const doctorIds = await doctorContract.getAllDoctors();
        const doctorsData = await Promise.all(
          doctorIds.map(async (doctorId) => {
            const doctor = await doctorContract.doctors(doctorId);
            const hasAccess = await patientContract.hasDoctorAccess(id, doctorId);
            return { id: doctorId, name: doctor.name, hasAccess };
          })
        );
        setDoctors(doctorsData);

        const allRecords = await doctorContract.getPatientRecords(id);
        setRecords(allRecords);
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, [doctorContract, patientContract, id]);

  const grantAccess = async (doctorId) => {
    try {
      const { doctorContract: signedDoctorContract, patientContract: signedPatientContract } = 
        await getSignedContracts();
      
      const tx1 = await signedPatientContract.grantAccessToDoctor(id, doctorId);
      await tx1.wait();
      
      const tx2 = await signedDoctorContract.addPatientAccess(doctorId, id);
      await tx2.wait();
      
      setDoctors(doctors.map(d => 
        d.id === doctorId ? { ...d, hasAccess: true } : d
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
      <h1 className="text-2xl mb-6">Patient Dashboard: {id}</h1>
      
      <div className="mb-8">
        <h2 className="text-xl mb-4">Available Doctors</h2>
        <div className="grid grid-cols-1 gap-4">
          {doctors.map(doctor => (
            <div key={doctor.id} className="p-4 border rounded flex justify-between items-center">
              <div>
                <p className="font-medium">{doctor.name}</p>
                <p className="text-sm text-gray-600">ID: {doctor.id}</p>
              </div>
              {!doctor.hasAccess && (
                <button 
                  onClick={() => grantAccess(doctor.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded"
                > Grant Access
                </button>
              )}
              {doctor.hasAccess && (
                <span className="text-green-600">Access Granted</span>
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
              <div className="flex justify-between items-start mb-2">
                <p className="font-medium">Dr. {record.doctorName}</p>
                <p className="text-sm text-gray-600">
                  {new Date(Number(record.timestamp) * 1000).toLocaleString()}
                </p>
              </div>
              <p>{record.message}</p>
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