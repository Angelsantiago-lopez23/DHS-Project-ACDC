// IndividualSearchService.js
import { invoke } from '@tauri-apps/api/tauri'; // Import Tauri's invoke method

export const set_search_input = async (search_input) => {
    try {
        console.log("Sending to Rust:", { searchInput: [search_input], searchType: 'individual' }); // Updated to camelCase
        const response = await invoke('set_search_input', { 
            searchInput: [search_input], // Key name updated to camelCase
            searchType: 'individual' // Key name updated to camelCase
        });
        return response;
    } catch (error) {
        throw new Error(`Tauri command error: ${error}`);
    }
};
