"""
Migration script to add parent_id column to tags table for hierarchical categories.
"""

import sqlite3
import os

def migrate_database():
    """Add parent_id column to tags table."""
    db_path = "data/recipes.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tags)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'parent_id' in columns:
            print("Column 'parent_id' already exists in tags table. No migration needed.")
        else:
            # Add parent_id column
            cursor.execute("""
                ALTER TABLE tags 
                ADD COLUMN parent_id INTEGER 
                REFERENCES tags(id)
            """)
            conn.commit()
            print("✓ Successfully added 'parent_id' column to tags table")
        
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
