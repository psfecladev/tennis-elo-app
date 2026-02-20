// API configuration
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Fetch rankings for a specific surface
 * @param {string} surface - Surface type (indoor_hard, outdoor_hard, clay, grass)
 * @param {number} limit - Number of players to return
 */
export async function fetchRankings(surface, limit = 100) {
    const response = await fetch(`${API_BASE}/api/rankings/${surface}?limit=${limit}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch rankings: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Fetch available surfaces
 */
export async function fetchSurfaces() {
    const response = await fetch(`${API_BASE}/api/surfaces`);
    if (!response.ok) {
        throw new Error(`Failed to fetch surfaces: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Fetch player details
 * @param {string} playerId - Player ID
 */
export async function fetchPlayer(playerId) {
    const response = await fetch(`${API_BASE}/api/players/${playerId}`);
    if (!response.ok) {
        if (response.status === 404) {
            return null;
        }
        throw new Error(`Failed to fetch player: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Search for players by name
 * @param {string} query - Search query
 */
export async function searchPlayers(query) {
    const response = await fetch(`${API_BASE}/api/players?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
        throw new Error(`Failed to search players: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Fetch system metadata
 */
export async function fetchMetadata() {
    const response = await fetch(`${API_BASE}/api/metadata`);
    if (!response.ok) {
        throw new Error(`Failed to fetch metadata: ${response.statusText}`);
    }
    return response.json();
}
