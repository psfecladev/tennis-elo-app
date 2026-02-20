import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/tennis_elo')
    
    # Kaggle
    KAGGLE_USERNAME = os.getenv('KAGGLE_USERNAME')
    KAGGLE_KEY = os.getenv('KAGGLE_KEY')
    KAGGLE_DATASET = 'dissfya/atp-tennis-2000-2023daily-pull'
    
    # Elo settings
    ELO_K_FACTOR = 32
    ELO_INITIAL_RATING = 1500
    
    # API
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
