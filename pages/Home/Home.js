import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center items-center space-y-10">
      <h1 className="text-gray-800 text-3xl font-semibold">
        County Records Inspector
      </h1>
      <img src={`${process.env.PUBLIC_URL}/dhs_logo.png`} alt="Department of Homeland Security Logo" className="w-32 h-auto" />
      <div className="flex space-x-4">
        <Link to="/individual">
          <button className="bg-transparent border-2 border-gray-800 text-gray-800 font-bold py-2 px-6 rounded hover:bg-gray-800 hover:text-white transition duration-200 ease-in-out">
            Individual Search
          </button>
        </Link>
        <Link to="/batch">
          <button className="bg-transparent border-2 border-gray-800 text-gray-800 font-bold py-2 px-6 rounded hover:bg-gray-800 hover:text-white transition duration-200 ease-in-out">
            Group Search
          </button>
        </Link>
      </div>
    </div>
  );
};

export default Home;
