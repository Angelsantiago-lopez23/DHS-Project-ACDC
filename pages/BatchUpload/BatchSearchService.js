// BatchSearchService.js
import { invoke } from '@tauri-apps/api/tauri';

export const set_search_input = async (searchInput) => { // Adjust argument to camelCase if needed
    try {
        const response = await invoke('set_search_input', {
            searchInput, // Update to camelCase if the backend expects this
            searchType: 'batch' // Update if the backend expects camelCase
        });
        return response; 
    } catch (error) {
        throw new Error(`Tauri command error: ${error}`);
    }
};
