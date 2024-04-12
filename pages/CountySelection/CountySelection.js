import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SubmissionForm = () => {
  const navigate = useNavigate();

  const initialCheckboxes = [
    { id: 1, label: 'Lee', isChecked: false },
    { id: 2, label: 'Collier', isChecked: false },
    { id: 3, label: 'Charlotte', isChecked: false },
    { id: 4, label: 'Hendry', isChecked: false },
    { id: 5, label: 'Clark', isChecked: false },
    { id: 6, label: 'Island', isChecked: false },
  ];

  const [sortedCheckboxes, setSortedCheckboxes] = useState([]);

  useEffect(() => {
      setSortedCheckboxes([...initialCheckboxes].sort((a, b) => a.label.localeCompare(b.label)));
  }, []); // eslint-disable-next-line react-hooks/exhaustive-deps

  const handleCheckboxChange = (id) => {
    setSortedCheckboxes(sortedCheckboxes.map(checkbox =>
      checkbox.id === id ? { ...checkbox, isChecked: !checkbox.isChecked } : checkbox
    ));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    navigate('/python');
  };

  return (
    <div className="relative h-screen bg-gray-50 flex justify-center items-center">
      <div className="absolute top-10 left-40 flex justify-center items-center">
        <img src={`${process.env.PUBLIC_URL}/dhs_logo.png`} alt="Department Logo" className="w-24 h-auto opacity-90 cursor-pointer" onClick={() => navigate('/')}/>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col items-center p-10 md:p-24 bg-white rounded-lg shadow border border-gray-200 mt-24">
        <p className="text-lg font-semibold text-gray-800 mb-8">Please select the counties you would like to include:</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-8">
          {sortedCheckboxes.map(({ id, label, isChecked }) => (
            <div key={id} className="flex items-center">
              <input
                type="checkbox"
                className="shrink-0 h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                checked={isChecked}
                onChange={() => handleCheckboxChange(id)}
                id={`checkbox-${id}`}
              />
              <label htmlFor={`checkbox-${id}`} className="ml-2 text-gray-700 cursor-pointer">{label}</label>
            </div>
          ))}
        </div>
        <button type="submit" className="bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded transition duration-200 ease-in-out">
          Submit Selections
        </button>
      </form>
    </div>
  );
};

export default SubmissionForm;
