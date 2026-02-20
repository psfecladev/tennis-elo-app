<script>
    import { page } from '$app/stores';
</script>

<nav>
    <div class="nav-content">
        <a href="/" class="logo">Tennis Elo Rankings</a>
        <div class="nav-links">
            <a href="/" class:active={$page.url.pathname === '/'}>Rankings</a>
        </div>
    </div>
</nav>

<main>
    <slot />
</main>

<footer>
    <p>Data updated daily from ATP match results. Elo ratings calculated per surface.</p>
</footer>

<style>
    :global(*) {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    :global(body) {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        background: #0f172a;
        color: #e2e8f0;
        min-height: 100vh;
    }

    nav {
        background: #1e293b;
        border-bottom: 1px solid #334155;
        padding: 1rem 2rem;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .nav-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .logo {
        font-size: 1.5rem;
        font-weight: bold;
        color: #22c55e;
        text-decoration: none;
    }

    .nav-links {
        display: flex;
        gap: 1.5rem;
    }

    .nav-links a {
        color: #94a3b8;
        text-decoration: none;
        transition: color 0.2s;
    }

    .nav-links a:hover,
    .nav-links a.active {
        color: #22c55e;
    }

    main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
        min-height: calc(100vh - 150px);
    }

    footer {
        background: #1e293b;
        border-top: 1px solid #334155;
        padding: 1.5rem 2rem;
        text-align: center;
        color: #64748b;
        font-size: 0.875rem;
    }
</style>
