#!/usr/bin/env python3
"""
Database migration script to add missing columns to the Recipe table.
This script will safely add any missing columns without affecting existing data.
"""

import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get the database URL from environment variables."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle Heroku's "postgres://" vs "postgresql://" difference
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    else:
        # Fallback for local development
        return 'sqlite:///recipes.db'

def migrate_sqlite_database():
    """Migrate SQLite database by adding missing columns."""
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('instance/recipes.db')
        cursor = conn.cursor()
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(recipe)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        # Define required columns
        required_columns = {
            'audio_url': 'TEXT',
            'views': 'INTEGER DEFAULT 0',
            'created_at': 'DATETIME'
        }
        
        # Add missing columns
        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                try:
                    cursor.execute(f"ALTER TABLE recipe ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Successfully added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Column {column_name} might already exist: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        print("✅ SQLite migration completed successfully!")
        
    except Exception as e:
        print(f"❌ SQLite migration failed: {e}")

def migrate_postgresql_database():
    """Migrate PostgreSQL database by adding missing columns."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Get current table schema
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'recipe'
            """))
            columns = [row[0] for row in result]
            
            print(f"Current columns: {columns}")
            
            # Define required columns
            required_columns = {
                'audio_url': 'VARCHAR(500)',
                'views': 'INTEGER DEFAULT 0',
                'created_at': 'TIMESTAMP'
            }
            
            # Add missing columns
            for column_name, column_type in required_columns.items():
                if column_name not in columns:
                    print(f"Adding column: {column_name}")
                    try:
                        conn.execute(text(f"ALTER TABLE recipe ADD COLUMN {column_name} {column_type}"))
                        print(f"✅ Successfully added column: {column_name}")
                    except Exception as e:
                        print(f"⚠️  Column {column_name} might already exist: {e}")
            
            conn.commit()
            print("✅ PostgreSQL migration completed successfully!")
            
    except Exception as e:
        print(f"❌ PostgreSQL migration failed: {e}")

def create_tables_if_not_exist():
    """Create tables if they don't exist."""
    try:
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Tables created successfully!")
            
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")

def main():
    """Main migration function."""
    print("🔄 Starting database migration...")
    
    database_url = get_database_url()
    print(f"Database URL: {database_url}")
    
    if 'sqlite' in database_url.lower():
        print("📁 Using SQLite database")
        migrate_sqlite_database()
    elif 'postgresql' in database_url.lower() or 'postgres' in database_url.lower():
        print("🐘 Using PostgreSQL database")
        migrate_postgresql_database()
    else:
        print("❓ Unknown database type, trying to create tables...")
        create_tables_if_not_exist()
    
    print("🎉 Migration process completed!")

if __name__ == "__main__":
    main()
