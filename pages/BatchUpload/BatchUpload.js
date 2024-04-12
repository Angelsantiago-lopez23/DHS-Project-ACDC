import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as XLSX from 'xlsx';
import Upload from './components/Upload'; // Ensure this path matches your project structure
import { set_search_input } from './BatchSearchService'; // Ensure this is correctly imported

const BatchUpload = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]); // Set the file to the state
    };

    const handleUploadNow = async () => {
        if (!file) {
            alert('Please upload a file first!');
            return;
        }

        const reader = new FileReader();
        reader.onload = async (e) => {
            const data = e.target.result;
            const workbook = XLSX.read(data, { type: 'binary' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            const list = json.map(row => row[0]).filter(value => value !== undefined && value !== null); // Convert the first column into a list

            try {
                const response = await set_search_input(list); // Send this list to the backend
                console.log(response); // Logging the response for now
                navigate('/submit'); // Navigate after successful upload
            } catch (error) {
                console.error('Failed to upload data:', error);
            }
        };
        reader.readAsBinaryString(file);
    };

    return (
        <div className="batch-upload flex flex-col justify-center items-center h-screen bg-gray-50 p-4">
            <img src={`${process.env.PUBLIC_URL}/dhs_logo.png`} alt="Department Logo" className="mb-8 w-32 h-auto" />
            <div className="w-full max-w-4xl">
                <Upload onFileChange={handleFileChange}/> {/* Here the Upload component is used */}
            </div>
            <div className="flex justify-end space-x-4 mt-4">
                <button
                    className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition duration-200 ease-in-out"
                    onClick={() => navigate('/')} // Navigate back or to another page on cancel
                >
                    Cancel
                </button>
                <button
                    className="bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-200 ease-in-out"
                    onClick={handleUploadNow} // Trigger file upload process
                >
                    Upload Now
                </button>
            </div>
        </div>
    );
};

export default BatchUpload;
