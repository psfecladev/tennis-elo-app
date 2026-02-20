"""
Elo rating system for tennis players.
Calculates and updates ratings per surface type.
"""

import math
from datetime import datetime
from sqlalchemy.orm import Session

from .config import Config
from .models import Player, EloRating, Match, Metadata


class EloCalculator:
    """
    Elo rating calculator with configurable K-factor.
    Uses standard Elo formula with per-surface tracking.
    """
    
    def __init__(self, k_factor=None, initial_rating=None):
        self.k_factor = k_factor or Config.ELO_K_FACTOR
        self.initial_rating = initial_rating or Config.ELO_INITIAL_RATING
    
    def expected_score(self, rating_a, rating_b):
        """
        Calculate expected score for player A against player B.
        Returns probability of A winning (0 to 1).
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    
    def calculate_new_ratings(self, winner_rating, loser_rating):
        """
        Calculate new ratings after a match.
        Returns tuple of (new_winner_rating, new_loser_rating).
        """
        expected_winner = self.expected_score(winner_rating, loser_rating)
        expected_loser = self.expected_score(loser_rating, winner_rating)
        
        # Winner gets full point (1), loser gets 0
        new_winner = winner_rating + self.k_factor * (1 - expected_winner)
        new_loser = loser_rating + self.k_factor * (0 - expected_loser)
        
        return new_winner, new_loser


def get_or_create_player(session: Session, player_data: dict) -> Player:
    """Get existing player or create new one."""
    player = session.query(Player).filter(
        Player.player_id == player_data['player_id']
    ).first()
    
    if not player:
        player = Player(
            player_id=player_data['player_id'],
            name=player_data['name'],
            country=player_data.get('country'),
            hand=player_data.get('hand'),
            height=player_data.get('height') if player_data.get('height') and not math.isnan(float(player_data.get('height', 0) or 0)) else None,
            birth_year=player_data.get('birth_year')
        )
        session.add(player)
        session.flush()
    
    return player


def get_or_create_elo_rating(session: Session, player_id: int, surface: str, initial_rating: float) -> EloRating:
    """Get existing Elo rating or create new one for player/surface."""
    elo = session.query(EloRating).filter(
        EloRating.player_id == player_id,
        EloRating.surface == surface
    ).first()
    
    if not elo:
        elo = EloRating(
            player_id=player_id,
            surface=surface,
            rating=initial_rating,
            peak_rating=initial_rating
        )
        session.add(elo)
        session.flush()
    
    return elo


def process_match(session: Session, match_data: dict, calculator: EloCalculator) -> Match:
    """
    Process a single match and update Elo ratings.
    Returns the created Match record.
    """
    surface = match_data['surface']
    match_date = match_data['match_date']
    
    # Check if match already processed
    existing = session.query(Match).filter(Match.match_id == match_data['match_id']).first()
    if existing:
        return existing
    
    # Get or create players
    winner = get_or_create_player(session, {
        'player_id': match_data['winner_id'],
        'name': match_data['winner_name'],
        'country': match_data.get('winner_country'),
        'hand': match_data.get('winner_hand'),
        'height': match_data.get('winner_height'),
        'birth_year': match_data.get('winner_birth_year')
    })
    
    loser = get_or_create_player(session, {
        'player_id': match_data['loser_id'],
        'name': match_data['loser_name'],
        'country': match_data.get('loser_country'),
        'hand': match_data.get('loser_hand'),
        'height': match_data.get('loser_height'),
        'birth_year': match_data.get('loser_birth_year')
    })
    
    # Get or create Elo ratings for this surface
    winner_elo = get_or_create_elo_rating(session, winner.id, surface, calculator.initial_rating)
    loser_elo = get_or_create_elo_rating(session, loser.id, surface, calculator.initial_rating)
    
    # Store ratings before update
    winner_elo_before = winner_elo.rating
    loser_elo_before = loser_elo.rating
    
    # Calculate new ratings
    new_winner_rating, new_loser_rating = calculator.calculate_new_ratings(
        winner_elo.rating, loser_elo.rating
    )
    
    # Update winner's Elo
    winner_elo.rating = new_winner_rating
    winner_elo.matches_played += 1
    winner_elo.wins += 1
    winner_elo.last_match_date = match_date
    winner_elo.updated_at = datetime.utcnow()
    if new_winner_rating > winner_elo.peak_rating:
        winner_elo.peak_rating = new_winner_rating
    
    # Update loser's Elo
    loser_elo.rating = new_loser_rating
    loser_elo.matches_played += 1
    loser_elo.losses += 1
    loser_elo.last_match_date = match_date
    loser_elo.updated_at = datetime.utcnow()
    
    # Create match record
    match = Match(
        match_id=match_data['match_id'],
        tournament_name=match_data.get('tournament_name', ''),
        surface=surface,
        match_date=match_date,
        round=match_data.get('round', ''),
        winner_id=winner.id,
        loser_id=loser.id,
        score=match_data.get('score', ''),
        winner_elo_before=winner_elo_before,
        loser_elo_before=loser_elo_before,
        winner_elo_after=new_winner_rating,
        loser_elo_after=new_loser_rating
    )
    session.add(match)
    
    return match


def process_all_matches(session: Session, matches: list, batch_size: int = 1000):
    """
    Process all matches and update Elo ratings.
    Uses batched commits for performance.
    """
    calculator = EloCalculator()
    total = len(matches)
    processed = 0
    
    print(f"Processing {total} matches...")
    
    for i, match_data in enumerate(matches):
        try:
            process_match(session, match_data, calculator)
            processed += 1
            
            # Batch commit
            if (i + 1) % batch_size == 0:
                session.commit()
                print(f"Processed {i + 1}/{total} matches...")
                
        except Exception as e:
            print(f"Error processing match {match_data.get('match_id')}: {e}")
            session.rollback()
            continue
    
    # Final commit
    session.commit()
    
    # Update metadata
    Metadata.set_value(session, 'last_update', datetime.utcnow().isoformat())
    Metadata.set_value(session, 'total_matches', str(processed))
    
    print(f"Completed processing {processed} matches")
    return processed


def get_rankings_by_surface(session: Session, surface: str, limit: int = 100):
    """
    Get player rankings for a specific surface.
    Returns list of players with their Elo ratings, sorted by rating.
    """
    results = session.query(Player, EloRating).join(
        EloRating, Player.id == EloRating.player_id
    ).filter(
        EloRating.surface == surface,
        EloRating.matches_played >= 5  # Minimum matches for ranking
    ).order_by(
        EloRating.rating.desc()
    ).limit(limit).all()
    
    rankings = []
    for rank, (player, elo) in enumerate(results, 1):
        rankings.append({
            'rank': rank,
            'player': player.to_dict(),
            'elo': elo.to_dict()
        })
    
    return rankings


def get_player_details(session: Session, player_id: str):
    """
    Get detailed player information including all surface ratings.
    """
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return None
    
    # Get all surface ratings
    ratings = session.query(EloRating).filter(
        EloRating.player_id == player.id
    ).all()
    
    # Get recent matches
    recent_matches = session.query(Match).filter(
        (Match.winner_id == player.id) | (Match.loser_id == player.id)
    ).order_by(Match.match_date.desc()).limit(20).all()
    
    match_history = []
    for match in recent_matches:
        is_winner = match.winner_id == player.id
        opponent = match.loser if is_winner else match.winner
        match_history.append({
            'match_id': match.match_id,
            'date': match.match_date.isoformat() if match.match_date else None,
            'tournament': match.tournament_name,
            'surface': match.surface,
            'round': match.round,
            'result': 'W' if is_winner else 'L',
            'opponent': opponent.name if opponent else 'Unknown',
            'score': match.score,
            'elo_change': (match.winner_elo_after - match.winner_elo_before) if is_winner 
                         else (match.loser_elo_after - match.loser_elo_before)
        })
    
    return {
        'player': player.to_dict(),
        'ratings': {r.surface: r.to_dict() for r in ratings},
        'recent_matches': match_history
    }
