import React from 'react';
import { useNavigate } from 'react-router-dom';
import { invoke } from '@tauri-apps/api/tauri';

const Python = () => {
    const navigate = useNavigate();

    const startPythonScript = async () => {
        try {
            const result = await invoke('run_python_script');
            console.log(result); // This will be the output from your Python script
        } catch (error) {
            console.error('Failed to run Python script:', error);
        }
    };

    return (
        <div className='min-h-screen bg-gray-100 flex flex-col justify-center items-center space-y-10'>
            <div className='flex space-x-4'>
                <button className='bg-transparent border-2 border-gray-800 text-gray-800 font-bold py-2 px-6 rounded hover:bg-gray-800 hover:text-white transition duration-200 ease-in-out' onClick={startPythonScript}>Start Python</button>
                <button className='bg-transparent border-2 border-gray-800 text-gray-800 font-bold py-2 px-6 rounded hover:bg-gray-800 hover:text-white transition duration-200 ease-in-out' onClick={() => navigate('/')} >Home</button>
            </div>
        </div>
    );
};

export default Python;
