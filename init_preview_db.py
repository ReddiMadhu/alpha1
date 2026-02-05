"""Initialize database with new preview tables"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.database import init_database

if __name__ == "__main__":
    print("Initializing database with preview tables...")
    init_database()
    print("Database initialized successfully!")
    print("Preview tables created: preview_sessions, preview_files")
