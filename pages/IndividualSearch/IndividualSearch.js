import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { set_search_input } from './IndividualSearchService'; // Make sure the path is correct

const IndividualSearch = () => {
    const [search_input, setSearchInput] = useState('');
    const navigate = useNavigate();

    const handleContinue = async () => {
        try {
            console.log(search_input)
            const data = await set_search_input(search_input);
            console.log(data)
            navigate('/submit'); // Navigate to another route as needed
        } catch (error) {
            console.error('Failed to fetch services:', error);
        }
    };

    return (
        <div className="flex flex-col justify-center items-center h-screen bg-gray-50">
            <img src={`${process.env.PUBLIC_URL}/dhs_logo.png`} alt="Department Logo" className="mb-8 w-32 h-auto" />
            <div className="w-72">
                <div className="relative w-full min-w-[200px] h-10">
                    <input
                        type="text"
                        className="peer w-full h-full bg-transparent text-blue-gray-700 font-sans font-normal outline outline-0 focus:outline-0 disabled:bg-blue-gray-50 disabled:border-0 transition-all placeholder-shown:border placeholder-shown:border-blue-gray-200 placeholder-shown:border-t-blue-gray-200 border focus:border-2 border-t-transparent focus:border-t-transparent text-sm px-3 py-2.5 rounded-[7px] border-blue-gray-200 focus:border-gray-900"
                        placeholder=" "
                        value={search_input}
                        onChange={(e) => setSearchInput(e.target.value)}
                    />
                    <label
                        className="flex w-full h-full select-none pointer-events-none absolute left-0 font-normal !overflow-visible truncate peer-placeholder-shown:text-blue-gray-500 leading-tight peer-focus:leading-tight peer-disabled:text-transparent peer-disabled:peer-placeholder-shown:text-blue-gray-500 transition-all -top-1.5 peer-placeholder-shown:text-sm text-[11px] peer-focus:text-[11px] before:content[' '] before:block before:box-border before:w-2.5 before:h-1.5 before:mt-[6.5px] before:mr-1 peer-placeholder-shown:before:border-transparent before:rounded-tl-md before:border-t peer-focus:before:border-t-2 before:border-l peer-focus:before:border-l-2 before:pointer-events-none before:transition-all peer-disabled:before:border-transparent after:content[' '] after:block after:flex-grow after:box-border after:w-2.5 after:h-1.5 after:mt-[6.5px] after:ml-1 peer-placeholder-shown:after:border-transparent after:rounded-tr-md after:border-t peer-focus:after:border-t-2 after:border-r peer-focus:after:border-r-2 after:pointer-events-none after:transition-all peer-disabled:after:border-transparent peer-placeholder-shown:leading-[3.75] text-gray-500 peer-focus:text-gray-900 before:border-blue-gray-200 peer-focus:before:!border-gray-900 after:border-blue-gray-200 peer-focus:after:!border-gray-900">
                            Entry Information
                    </label>
                </div>
            </div>  
            <button
                className="mt-6 bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-200 ease-in-out"
                onClick={handleContinue}
            >
                Continue
            </button>
        </div>
    );
};

export default IndividualSearch;
