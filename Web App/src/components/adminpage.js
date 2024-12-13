import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Admin = ({ getSignedContracts }) => {
  const [doctorId, setDoctorId] = useState('');
  const [doctorName, setDoctorName] = useState('');
  const [patientId, setPatientId] = useState('');
  const [patientName, setPatientName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const registerDoctor = async (e) => {
    e.preventDefault();
    try {
      const { doctorContract } = await getSignedContracts();
      const tx = await doctorContract.registerDoctor(doctorId, doctorName);
      await tx.wait();
      setSuccess('Doctor registered successfully');
      setDoctorId('');
      setDoctorName('');
      setError('');
    } catch (err) {
      setError(err.message || 'Error registering doctor');
    }
  };

  const registerPatient = async (e) => {
    e.preventDefault();
    try {
      const { patientContract } = await getSignedContracts();
      const tx = await patientContract.registerPatient(patientId, patientName);
      await tx.wait();
      setSuccess('Patient registered successfully');
      setPatientId('');
      setPatientName('');
      setError('');
    } catch (err) {
      setError(err.message || 'Error registering patient');
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl mb-6">Admin Dashboard</h1>
      <button onClick={() => navigate('/')} className="mb-4 px-4 py-2 bg-gray-600 text-white rounded">
        Back to Home
      </button>
      
      {error && <p className="text-red-500 mb-4">{error}</p>}
      {success && <p className="text-green-500 mb-4">{success}</p>}
      
      <div className="grid grid-cols-2 gap-6">
        <form onSubmit={registerDoctor} className="space-y-4">
          <h2 className="text-xl">Register Doctor</h2>
          <input
            type="text"
            placeholder="Doctor ID"
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <input
            type="text"
            placeholder="Doctor Name"
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded">
            Register Doctor
          </button>
        </form>

        <form onSubmit={registerPatient} className="space-y-4">
          <h2 className="text-xl">Register Patient</h2>
          <input
            type="text"
            placeholder="Patient ID"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <input
            type="text"
            placeholder="Patient Name"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <button type="submit" className="w-full py-2 bg-green-600 text-white rounded">
            Register Patient
          </button>
        </form>
      </div>
    </div>
  );
};

export default Admin;