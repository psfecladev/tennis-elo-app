"""
Flask API for Tennis Elo rankings.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from .config import Config
from .models import SessionLocal, Metadata, init_db
from .elo import get_rankings_by_surface, get_player_details

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Valid surfaces
VALID_SURFACES = ['indoor_hard', 'outdoor_hard', 'clay', 'grass']


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/api/surfaces', methods=['GET'])
def get_surfaces():
    """Get list of available surfaces."""
    return jsonify({
        'surfaces': [
            {'id': 'indoor_hard', 'name': 'Indoor Hard', 'color': '#3b82f6'},
            {'id': 'outdoor_hard', 'name': 'Outdoor Hard', 'color': '#06b6d4'},
            {'id': 'clay', 'name': 'Clay', 'color': '#f97316'},
            {'id': 'grass', 'name': 'Grass', 'color': '#22c55e'}
        ]
    })


@app.route('/api/rankings/<surface>', methods=['GET'])
def get_rankings(surface):
    """
    Get rankings for a specific surface.
    
    Query params:
        limit: Number of players to return (default 100)
    """
    if surface not in VALID_SURFACES:
        return jsonify({'error': f'Invalid surface. Must be one of: {VALID_SURFACES}'}), 400
    
    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 500)  # Cap at 500
    
    session = SessionLocal()
    try:
        rankings = get_rankings_by_surface(session, surface, limit)
        return jsonify({
            'surface': surface,
            'rankings': rankings,
            'count': len(rankings)
        })
    finally:
        session.close()


@app.route('/api/players/<player_id>', methods=['GET'])
def get_player(player_id):
    """Get detailed information for a specific player."""
    session = SessionLocal()
    try:
        player_data = get_player_details(session, player_id)
        if not player_data:
            return jsonify({'error': 'Player not found'}), 404
        return jsonify(player_data)
    finally:
        session.close()


@app.route('/api/players', methods=['GET'])
def search_players():
    """
    Search for players by name.
    
    Query params:
        q: Search query
        limit: Number of results (default 20)
    """
    from .models import Player
    
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    session = SessionLocal()
    try:
        players = session.query(Player).filter(
            Player.name.ilike(f'%{query}%')
        ).limit(limit).all()
        
        return jsonify({
            'query': query,
            'results': [p.to_dict() for p in players],
            'count': len(players)
        })
    finally:
        session.close()


@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Get system metadata including last update time."""
    session = SessionLocal()
    try:
        last_update = Metadata.get_value(session, 'last_update')
        total_matches = Metadata.get_value(session, 'total_matches')
        
        return jsonify({
            'last_update': last_update,
            'total_matches': int(total_matches) if total_matches else 0
        })
    finally:
        session.close()


def create_app():
    """Application factory."""
    init_db()
    return app


# Initialize database tables on module load (for gunicorn)
init_db()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
