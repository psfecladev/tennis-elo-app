#!/usr/bin/env python3
"""
Daily update script for Tennis Elo ratings.
Downloads latest data from Kaggle and updates the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import init_db, SessionLocal
from app.data_pipeline import download_dataset, load_and_process_data, get_match_records
from app.elo import process_all_matches


def run_update():
    """Run the daily update process."""
    print("=" * 60)
    print("Tennis Elo Daily Update")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    # Download latest data
    print("\n2. Downloading latest dataset from Kaggle...")
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    csv_path = download_dataset(data_dir)
    
    # Process data
    print("\n3. Processing match data...")
    df = load_and_process_data(csv_path)
    matches = get_match_records(df)
    
    # Update Elo ratings
    print("\n4. Updating Elo ratings...")
    session = SessionLocal()
    try:
        processed = process_all_matches(session, matches)
        print(f"\nSuccessfully processed {processed} matches")
    finally:
        session.close()
    
    # Cleanup
    print("\n5. Cleaning up temporary files...")
    if os.path.exists(csv_path):
        os.remove(csv_path)
    
    print("\n" + "=" * 60)
    print("Update completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    run_update()
