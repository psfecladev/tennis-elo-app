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
    
    Uses Surface and Court columns from dataset.
    """
    # Get surface type (Hard, Clay, Grass)
    surface = str(row.get('Surface', '')).lower().strip()
    # Get court type (Indoor, Outdoor)
    court = str(row.get('Court', '')).lower().strip()
    tournament = str(row.get('Tournament', '')).lower().strip()
    
    # Grass courts
    if surface == 'grass' or any(t in tournament for t in GRASS_TOURNAMENTS):
        return 'grass'
    
    # Clay courts
    if surface == 'clay':
        return 'clay'
    
    # Hard courts - determine indoor vs outdoor using Court column
    if surface == 'hard' or surface == 'carpet':
        # Use Court column if available
        if court == 'indoor':
            return 'indoor_hard'
        elif court == 'outdoor':
            return 'outdoor_hard'
        
        # Fallback: Check if indoor based on tournament name
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
    
    Expected CSV columns: Tournament,Date,Series,Court,Surface,Round,Best of,
                         Player_1,Player_2,Winner,Rank_1,Rank_2,Pts_1,Pts_2,
                         Odd_1,Odd_2,Score
    """
    print(f"Loading data from {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path, low_memory=False)
    
    print(f"Loaded {len(df)} matches")
    print(f"Columns: {list(df.columns)}")
    
    # Parse dates - the Date column is in YYYY-MM-DD format
    if 'Date' in df.columns:
        df['match_date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
    else:
        raise ValueError("CSV missing 'Date' column")
    
    # Classify surfaces using Surface and Court columns
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
    
    CSV format has Player_1, Player_2, Winner columns with player names.
    Winner column matches either Player_1 or Player_2.
    """
    matches = []
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            # Get player names
            player_1 = str(row.get('Player_1', '')).strip()
            player_2 = str(row.get('Player_2', '')).strip()
            winner_name = str(row.get('Winner', '')).strip()
            
            # Skip if missing required fields
            if not player_1 or not player_2 or not winner_name:
                skipped += 1
                continue
            if player_1 == 'nan' or player_2 == 'nan':
                skipped += 1
                continue
            
            # Determine winner and loser based on Winner column
            if winner_name == player_1:
                winner = player_1
                loser = player_2
            elif winner_name == player_2:
                winner = player_2
                loser = player_1
            else:
                # Winner doesn't match either player - skip
                skipped += 1
                continue
            
            # Skip invalid dates
            if pd.isna(row.get('match_date')):
                skipped += 1
                continue
            
            # Generate player IDs from names (use name as ID since dataset doesn't have IDs)
            # Normalize names for consistent ID generation
            winner_id = winner.lower().replace(' ', '_').replace('.', '').replace("'", '')
            loser_id = loser.lower().replace(' ', '_').replace('.', '').replace("'", '')
            
            # Create unique match ID
            match_date_str = row['match_date'].strftime('%Y%m%d') if not pd.isna(row['match_date']) else str(idx)
            tournament = str(row.get('Tournament', '')).strip()
            match_id = f"{match_date_str}_{tournament}_{winner_id}_{loser_id}"
            
            match = {
                'match_id': match_id,
                'tournament_name': tournament,
                'surface': row['classified_surface'],
                'match_date': row['match_date'],
                'round': str(row.get('Round', '')),
                'winner_id': winner_id,
                'winner_name': winner,
                'winner_country': '',  # Not in dataset
                'winner_hand': '',     # Not in dataset
                'winner_height': None, # Not in dataset
                'winner_birth_year': None,  # Not in dataset
                'winner_rank': row.get('Rank_1') if winner_name == player_1 else row.get('Rank_2'),
                'loser_id': loser_id,
                'loser_name': loser,
                'loser_country': '',   # Not in dataset
                'loser_hand': '',      # Not in dataset
                'loser_height': None,  # Not in dataset
                'loser_birth_year': None,   # Not in dataset
                'loser_rank': row.get('Rank_2') if winner_name == player_1 else row.get('Rank_1'),
                'score': str(row.get('Score', '')),
            }
                
            matches.append(match)
            
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            skipped += 1
            continue
    
    print(f"Extracted {len(matches)} valid matches (skipped {skipped})")
    return matches
