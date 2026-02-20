<script>
    import { onMount } from 'svelte';
    import { fetchRankings, fetchMetadata, searchPlayers } from '$lib/api.js';

    // Surfaces configuration
    const surfaces = [
        { id: 'indoor_hard', name: 'Indoor Hard', color: '#3b82f6' },
        { id: 'outdoor_hard', name: 'Outdoor Hard', color: '#06b6d4' },
        { id: 'clay', name: 'Clay', color: '#f97316' },
        { id: 'grass', name: 'Grass', color: '#22c55e' }
    ];

    let selectedSurface = 'outdoor_hard';
    let rankings = [];
    let loading = true;
    let error = null;
    let metadata = null;
    let searchQuery = '';
    let searchResults = [];
    let showSearch = false;

    async function loadRankings(surface) {
        loading = true;
        error = null;
        try {
            const data = await fetchRankings(surface);
            rankings = data.rankings;
        } catch (e) {
            error = e.message;
            rankings = [];
        } finally {
            loading = false;
        }
    }

    async function handleSearch() {
        if (searchQuery.length < 2) {
            searchResults = [];
            return;
        }
        try {
            const data = await searchPlayers(searchQuery);
            searchResults = data.results;
            showSearch = true;
        } catch (e) {
            searchResults = [];
        }
    }

    function selectSurface(surface) {
        selectedSurface = surface;
        loadRankings(surface);
    }

    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    onMount(async () => {
        loadRankings(selectedSurface);
        try {
            metadata = await fetchMetadata();
        } catch (e) {
            console.error('Failed to load metadata:', e);
        }
    });
</script>

<svelte:head>
    <title>Tennis Elo Rankings - {surfaces.find(s => s.id === selectedSurface)?.name}</title>
</svelte:head>

<div class="container">
    <header>
        <h1>ATP Elo Rankings</h1>
        {#if metadata?.last_update}
            <p class="update-info">Last updated: {formatDate(metadata.last_update)}</p>
        {/if}
    </header>

    <!-- Search -->
    <div class="search-container">
        <input 
            type="text" 
            placeholder="Search players..." 
            bind:value={searchQuery}
            on:input={handleSearch}
            on:focus={() => showSearch = searchQuery.length >= 2}
            on:blur={() => setTimeout(() => showSearch = false, 200)}
        />
        {#if showSearch && searchResults.length > 0}
            <div class="search-results">
                {#each searchResults as player}
                    <a href="/player/{player.player_id}" class="search-result">
                        <span class="player-name">{player.name}</span>
                        <span class="player-country">{player.country || ''}</span>
                    </a>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Surface Selector -->
    <div class="surface-selector">
        {#each surfaces as surface}
            <button 
                class="surface-btn" 
                class:active={selectedSurface === surface.id}
                style="--surface-color: {surface.color}"
                on:click={() => selectSurface(surface.id)}
            >
                {surface.name}
            </button>
        {/each}
    </div>

    <!-- Rankings Table -->
    {#if loading}
        <div class="loading">Loading rankings...</div>
    {:else if error}
        <div class="error">{error}</div>
    {:else if rankings.length === 0}
        <div class="empty">No rankings available for this surface.</div>
    {:else}
        <div class="rankings-table">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Player</th>
                        <th>Country</th>
                        <th>Elo Rating</th>
                        <th>Peak</th>
                        <th>W-L</th>
                        <th>Last Match</th>
                    </tr>
                </thead>
                <tbody>
                    {#each rankings as item}
                        <tr>
                            <td class="rank">{item.rank}</td>
                            <td class="player">
                                <a href="/player/{item.player.player_id}">{item.player.name}</a>
                            </td>
                            <td class="country">{item.player.country || '-'}</td>
                            <td class="rating">{item.elo.rating}</td>
                            <td class="peak">{item.elo.peak_rating}</td>
                            <td class="record">{item.elo.wins}-{item.elo.losses}</td>
                            <td class="last-match">{formatDate(item.elo.last_match_date)}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .container {
        max-width: 1000px;
        margin: 0 auto;
    }

    header {
        text-align: center;
        margin-bottom: 2rem;
    }

    h1 {
        font-size: 2rem;
        color: #f8fafc;
        margin-bottom: 0.5rem;
    }

    .update-info {
        color: #64748b;
        font-size: 0.875rem;
    }

    .search-container {
        position: relative;
        margin-bottom: 1.5rem;
    }

    .search-container input {
        width: 100%;
        padding: 0.75rem 1rem;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 0.5rem;
        color: #e2e8f0;
        font-size: 1rem;
    }

    .search-container input:focus {
        outline: none;
        border-color: #22c55e;
    }

    .search-results {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 0.5rem;
        max-height: 300px;
        overflow-y: auto;
        z-index: 50;
    }

    .search-result {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        color: #e2e8f0;
        text-decoration: none;
        border-bottom: 1px solid #334155;
    }

    .search-result:hover {
        background: #334155;
    }

    .search-result:last-child {
        border-bottom: none;
    }

    .player-country {
        color: #64748b;
    }

    .surface-selector {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }

    .surface-btn {
        flex: 1;
        min-width: 120px;
        padding: 0.75rem 1.5rem;
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 0.5rem;
        color: #94a3b8;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .surface-btn:hover {
        border-color: var(--surface-color);
        color: var(--surface-color);
    }

    .surface-btn.active {
        background: var(--surface-color);
        border-color: var(--surface-color);
        color: white;
    }

    .loading, .error, .empty {
        text-align: center;
        padding: 3rem;
        color: #64748b;
    }

    .error {
        color: #ef4444;
    }

    .rankings-table {
        background: #1e293b;
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid #334155;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th {
        background: #0f172a;
        padding: 1rem;
        text-align: left;
        font-weight: 600;
        color: #94a3b8;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    td {
        padding: 1rem;
        border-bottom: 1px solid #334155;
    }

    tr:last-child td {
        border-bottom: none;
    }

    tr:hover {
        background: #334155;
    }

    .rank {
        font-weight: bold;
        color: #64748b;
        width: 60px;
    }

    .player a {
        color: #22c55e;
        text-decoration: none;
        font-weight: 500;
    }

    .player a:hover {
        text-decoration: underline;
    }

    .country {
        color: #64748b;
    }

    .rating {
        font-weight: bold;
        color: #f8fafc;
        font-size: 1.1rem;
    }

    .peak {
        color: #94a3b8;
    }

    .record {
        color: #94a3b8;
    }

    .last-match {
        color: #64748b;
        font-size: 0.875rem;
    }

    @media (max-width: 768px) {
        .surface-btn {
            min-width: calc(50% - 0.5rem);
        }

        th, td {
            padding: 0.75rem 0.5rem;
            font-size: 0.875rem;
        }

        .peak, .last-match {
            display: none;
        }
    }
</style>
