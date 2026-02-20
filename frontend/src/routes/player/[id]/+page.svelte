<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { fetchPlayer } from '$lib/api.js';

    // Surfaces configuration
    const surfaces = [
        { id: 'indoor_hard', name: 'Indoor Hard', color: '#3b82f6' },
        { id: 'outdoor_hard', name: 'Outdoor Hard', color: '#06b6d4' },
        { id: 'clay', name: 'Clay', color: '#f97316' },
        { id: 'grass', name: 'Grass', color: '#22c55e' }
    ];

    let player = null;
    let ratings = {};
    let recentMatches = [];
    let loading = true;
    let error = null;

    function getSurfaceColor(surfaceId) {
        return surfaces.find(s => s.id === surfaceId)?.color || '#64748b';
    }

    function getSurfaceName(surfaceId) {
        return surfaces.find(s => s.id === surfaceId)?.name || surfaceId;
    }

    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    function formatEloChange(change) {
        if (change === null || change === undefined) return '';
        const rounded = Math.round(change);
        if (rounded > 0) return `+${rounded}`;
        return rounded.toString();
    }

    onMount(async () => {
        const playerId = $page.params.id;
        try {
            const data = await fetchPlayer(playerId);
            if (!data) {
                error = 'Player not found';
            } else {
                player = data.player;
                ratings = data.ratings || {};
                recentMatches = data.recent_matches || [];
            }
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });
</script>

<svelte:head>
    <title>{player?.name || 'Player'} - Tennis Elo Rankings</title>
</svelte:head>

<div class="container">
    <a href="/" class="back-link">&larr; Back to Rankings</a>

    {#if loading}
        <div class="loading">Loading player data...</div>
    {:else if error}
        <div class="error">{error}</div>
    {:else if player}
        <!-- Player Header -->
        <header class="player-header">
            <h1>{player.name}</h1>
            {#if player.country}
                <span class="country">{player.country}</span>
            {/if}
        </header>

        <!-- Surface Ratings -->
        <section class="ratings-section">
            <h2>Surface Ratings</h2>
            <div class="ratings-grid">
                {#each surfaces as surface}
                    {@const rating = ratings[surface.id]}
                    <div class="rating-card" style="--surface-color: {surface.color}">
                        <div class="surface-name">{surface.name}</div>
                        {#if rating && rating.matches >= 5}
                            <div class="rating-value">{rating.rating}</div>
                            <div class="rating-details">
                                <span class="peak">Peak: {rating.peak_rating}</span>
                                <span class="record">{rating.wins}W - {rating.losses}L</span>
                            </div>
                        {:else if rating}
                            <div class="rating-value muted">{rating.rating}</div>
                            <div class="rating-details">
                                <span class="insufficient">Needs {5 - rating.matches} more matches</span>
                            </div>
                        {:else}
                            <div class="rating-value muted">—</div>
                            <div class="rating-details">
                                <span class="no-matches">No matches</span>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        </section>

        <!-- Recent Matches -->
        <section class="matches-section">
            <h2>Recent Matches</h2>
            {#if recentMatches.length === 0}
                <p class="no-matches">No recent match data available.</p>
            {:else}
                <div class="matches-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Tournament</th>
                                <th>Surface</th>
                                <th>Round</th>
                                <th>Result</th>
                                <th>Opponent</th>
                                <th>Score</th>
                                <th>Elo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each recentMatches as match}
                                <tr>
                                    <td class="date">{formatDate(match.date)}</td>
                                    <td class="tournament">{match.tournament || '-'}</td>
                                    <td>
                                        <span 
                                            class="surface-badge" 
                                            style="background-color: {getSurfaceColor(match.surface)}"
                                        >
                                            {getSurfaceName(match.surface)}
                                        </span>
                                    </td>
                                    <td class="round">{match.round || '-'}</td>
                                    <td class="result {match.result === 'W' ? 'win' : 'loss'}">
                                        {match.result}
                                    </td>
                                    <td class="opponent">{match.opponent}</td>
                                    <td class="score">{match.score || '-'}</td>
                                    <td class="elo-change {match.elo_change > 0 ? 'positive' : 'negative'}">
                                        {formatEloChange(match.elo_change)}
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </section>
    {/if}
</div>

<style>
    .container {
        max-width: 1000px;
        margin: 0 auto;
    }

    .back-link {
        display: inline-block;
        margin-bottom: 1.5rem;
        color: #22c55e;
        text-decoration: none;
        font-size: 0.875rem;
    }

    .back-link:hover {
        text-decoration: underline;
    }

    .loading, .error {
        text-align: center;
        padding: 3rem;
        color: #64748b;
    }

    .error {
        color: #ef4444;
    }

    /* Player Header */
    .player-header {
        margin-bottom: 2rem;
    }

    .player-header h1 {
        font-size: 2.5rem;
        color: #f8fafc;
        margin-bottom: 0.5rem;
    }

    .country {
        color: #64748b;
        font-size: 1.125rem;
    }

    /* Ratings Section */
    .ratings-section {
        margin-bottom: 3rem;
    }

    .ratings-section h2 {
        font-size: 1.25rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }

    .ratings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .rating-card {
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 0.75rem;
        padding: 1.25rem;
        text-align: center;
        transition: border-color 0.2s;
    }

    .rating-card:hover {
        border-color: var(--surface-color);
    }

    .surface-name {
        color: var(--surface-color);
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .rating-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #f8fafc;
        margin-bottom: 0.5rem;
    }

    .rating-value.muted {
        color: #475569;
    }

    .rating-details {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.875rem;
        color: #64748b;
    }

    .peak {
        color: #94a3b8;
    }

    .record {
        color: #64748b;
    }

    .insufficient, .no-matches {
        color: #475569;
        font-style: italic;
    }

    /* Matches Section */
    .matches-section h2 {
        font-size: 1.25rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }

    .matches-table {
        background: #1e293b;
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid #334155;
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        min-width: 700px;
    }

    th {
        background: #0f172a;
        padding: 0.875rem 1rem;
        text-align: left;
        font-weight: 600;
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    td {
        padding: 0.875rem 1rem;
        border-bottom: 1px solid #334155;
        font-size: 0.875rem;
    }

    tr:last-child td {
        border-bottom: none;
    }

    tr:hover {
        background: #334155;
    }

    .date {
        color: #64748b;
        white-space: nowrap;
    }

    .tournament {
        color: #e2e8f0;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .surface-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        color: white;
        white-space: nowrap;
    }

    .round {
        color: #94a3b8;
    }

    .result {
        font-weight: bold;
        width: 40px;
    }

    .result.win {
        color: #22c55e;
    }

    .result.loss {
        color: #ef4444;
    }

    .opponent {
        color: #e2e8f0;
    }

    .score {
        color: #94a3b8;
        font-family: monospace;
    }

    .elo-change {
        font-weight: 600;
        text-align: right;
    }

    .elo-change.positive {
        color: #22c55e;
    }

    .elo-change.negative {
        color: #ef4444;
    }

    p.no-matches {
        color: #64748b;
        text-align: center;
        padding: 2rem;
    }

    @media (max-width: 768px) {
        .player-header h1 {
            font-size: 1.75rem;
        }

        .rating-value {
            font-size: 2rem;
        }

        th, td {
            padding: 0.625rem 0.5rem;
        }
    }
</style>
