from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime

from .config import Config

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Player(Base):
    """Player model storing basic player info."""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country = Column(String(10))
    hand = Column(String(10))
    height = Column(Integer)
    birth_year = Column(Integer)
    
    # Relationships
    elo_ratings = relationship('EloRating', back_populates='player')
    matches_won = relationship('Match', foreign_keys='Match.winner_id', back_populates='winner')
    matches_lost = relationship('Match', foreign_keys='Match.loser_id', back_populates='loser')
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'name': self.name,
            'country': self.country,
            'hand': self.hand,
            'height': self.height,
            'birth_year': self.birth_year
        }


class EloRating(Base):
    """Elo rating per player per surface."""
    __tablename__ = 'elo_ratings'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    surface = Column(String(20), nullable=False)  # indoor_hard, outdoor_hard, clay, grass
    rating = Column(Float, default=1500.0)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    peak_rating = Column(Float, default=1500.0)
    last_match_date = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    player = relationship('Player', back_populates='elo_ratings')
    
    __table_args__ = (
        UniqueConstraint('player_id', 'surface', name='unique_player_surface'),
        Index('idx_surface_rating', 'surface', 'rating'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'surface': self.surface,
            'rating': round(self.rating, 1),
            'matches_played': self.matches_played,
            'wins': self.wins,
            'losses': self.losses,
            'peak_rating': round(self.peak_rating, 1),
            'last_match_date': self.last_match_date.isoformat() if self.last_match_date else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Match(Base):
    """Match history for tracking and recalculation."""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(100), unique=True, nullable=False)
    tournament_name = Column(String(200))
    surface = Column(String(20), nullable=False)
    match_date = Column(DateTime, nullable=False, index=True)
    round = Column(String(50))
    winner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    loser_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    score = Column(String(100))
    winner_elo_before = Column(Float)
    loser_elo_before = Column(Float)
    winner_elo_after = Column(Float)
    loser_elo_after = Column(Float)
    
    # Relationships
    winner = relationship('Player', foreign_keys=[winner_id], back_populates='matches_won')
    loser = relationship('Player', foreign_keys=[loser_id], back_populates='matches_lost')
    
    __table_args__ = (
        Index('idx_match_date', 'match_date'),
    )


class Metadata(Base):
    """System metadata for tracking updates."""
    __tablename__ = 'metadata'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_value(cls, session, key):
        record = session.query(cls).filter(cls.key == key).first()
        return record.value if record else None
    
    @classmethod
    def set_value(cls, session, key, value):
        record = session.query(cls).filter(cls.key == key).first()
        if record:
            record.value = value
            record.updated_at = datetime.utcnow()
        else:
            record = cls(key=key, value=value)
            session.add(record)
        session.commit()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
