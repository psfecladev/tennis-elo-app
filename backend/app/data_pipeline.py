"""
Data pipeline for downloading and processing ATP tennis data from Kaggle.
Handles surface classification into four categories.
"""

import os
import pandas as pd
from datetime import datetime
from kaggle.api.kaggle_api_extended import KaggleApi

from .config import Config


# Surface classification rules - known indoor tournaments
INDOOR_TOURNAMENTS = {
    'paris masters', 'vienna', 'basel', 'stockholm', 'st. petersburg',
    'antwerp', 'metz', 'moscow', 'marseille', 'montpellier', 'rotterdam',
    'sofia', 'atp finals', 'next gen finals', 'davis cup finals'
}

# Known grass tournaments
GRASS_TOURNAMENTS = {
    'wimbledon', 'halle', 'queens', "queen's club", 'stuttgart',
    'eastbourne', 's-hertogenbosch', 'newport', 'mallorca'
}


def classify_surface(row):
    """
    Classify match surface into one of four categories:
    - indoor_hard: Indoor hard court matches
    - outdoor_hard: Outdoor hard court matches  
    - clay: Clay court matches
    - grass: Grass court matches
    
    Uses tournament name and surface column from dataset.
    """
    surface = str(row.get('surface', '')).lower().strip()
    tournament = str(row.get('tourney_name', '')).lower().strip()
    
    # Grass courts
    if surface == 'grass' or any(t in tournament for t in GRASS_TOURNAMENTS):
        return 'grass'
    
    # Clay courts
    if surface == 'clay':
        return 'clay'
    
    # Hard courts - determine indoor vs outdoor
    if surface == 'hard' or surface == 'carpet':
        # Check if indoor based on tournament name
        if any(t in tournament for t in INDOOR_TOURNAMENTS):
            return 'indoor_hard'
        
        # Check for indoor indicator in tournament name
        if 'indoor' in tournament:
            return 'indoor_hard'
        
        # Default hard courts to outdoor
        return 'outdoor_hard'
    
    # Fallback - try to infer from tournament
    if any(t in tournament for t in INDOOR_TOURNAMENTS):
        return 'indoor_hard'
    
    # Default unknown to outdoor hard
    return 'outdoor_hard'


def download_dataset(data_dir='data'):
    """
    Download ATP tennis dataset from Kaggle.
    Returns path to the downloaded CSV file.
    """
    os.makedirs(data_dir, exist_ok=True)
    
    # Configure Kaggle API
    api = KaggleApi()
    api.authenticate()
    
    print(f"Downloading dataset: {Config.KAGGLE_DATASET}")
    
    # Download dataset
    api.dataset_download_files(
        Config.KAGGLE_DATASET,
        path=data_dir,
        unzip=True
    )
    
    # Find the CSV file
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError("No CSV file found in downloaded dataset")
    
    csv_path = os.path.join(data_dir, csv_files[0])
    print(f"Dataset downloaded: {csv_path}")
    
    return csv_path


def load_and_process_data(csv_path):
    """
    Load CSV and process into structured match data.
    Returns DataFrame with classified surfaces.
    """
    print(f"Loading data from {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path, low_memory=False)
    
    print(f"Loaded {len(df)} matches")
    
    # Parse dates
    if 'tourney_date' in df.columns:
        df['match_date'] = pd.to_datetime(df['tourney_date'], format='%Y%m%d', errors='coerce')
    
    # Classify surfaces
    df['classified_surface'] = df.apply(classify_surface, axis=1)
    
    # Sort by date
    df = df.sort_values('match_date')
    
    # Print surface distribution
    print("\nSurface distribution:")
    print(df['classified_surface'].value_counts())
    
    return df


def get_match_records(df):
    """
    Extract match records from DataFrame.
    Returns list of match dictionaries ready for Elo processing.
    """
    matches = []
    
    for _, row in df.iterrows():
        try:
            match = {
                'match_id': f"{row.get('tourney_id', '')}_{row.get('match_num', '')}",
                'tournament_name': row.get('tourney_name', ''),
                'surface': row['classified_surface'],
                'match_date': row['match_date'],
                'round': row.get('round', ''),
                'winner_id': str(row.get('winner_id', '')),
                'winner_name': row.get('winner_name', ''),
                'winner_country': row.get('winner_ioc', ''),
                'winner_hand': row.get('winner_hand', ''),
                'winner_height': row.get('winner_ht'),
                'winner_birth_year': row.get('winner_age'),
                'loser_id': str(row.get('loser_id', '')),
                'loser_name': row.get('loser_name', ''),
                'loser_country': row.get('loser_ioc', ''),
                'loser_hand': row.get('loser_hand', ''),
                'loser_height': row.get('loser_ht'),
                'loser_birth_year': row.get('loser_age'),
                'score': row.get('score', ''),
            }
            
            # Skip invalid matches
            if pd.isna(row['match_date']):
                continue
            if not match['winner_id'] or not match['loser_id']:
                continue
            if match['winner_id'] == 'nan' or match['loser_id'] == 'nan':
                continue
                
            matches.append(match)
            
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    print(f"Extracted {len(matches)} valid matches")
    return matches
