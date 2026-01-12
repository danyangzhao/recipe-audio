#!/usr/bin/env python3
"""
Database migration script to ensure all tables exist.
Run this before starting the app on a fresh database.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get the database URL from environment variables."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle Railway/Heroku's "postgres://" vs "postgresql://" difference
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    return 'sqlite:///recipes.db'

def main():
    """Create all database tables."""
    print("🔄 Starting database migration...")
    
    database_url = get_database_url()
    db_type = "PostgreSQL" if "postgresql" in database_url else "SQLite"
    print(f"📁 Using {db_type} database")
    
    try:
        from app import app, db
        
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    
    print("🎉 Migration completed!")

if __name__ == "__main__":
    main()
