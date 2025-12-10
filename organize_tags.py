"""
Script to organize existing flat tags into a hierarchy.
"""

import sqlite3

def organize_tags():
    """Reorganize tags into a logical hierarchy."""
    conn = sqlite3.connect("data/recipes.db")
    cursor = conn.cursor()
    
    try:
        # Define the hierarchy structure
        # Format: child_name -> parent_name
        hierarchy = {
            'pasta': 'Italian',
            'pizza': 'Italian',
            'italian': 'Italian',  # Merge duplicate
            'beef': 'Meat',
            'chicken': 'Meat',
            'pork': 'Meat',
            'fish': 'Seafood',
            'shrimp': 'Seafood',
            'sausage': 'Meat',
            'cherry': 'dessert',
        }
        
        # Create main categories if they don't exist
        main_categories = ['Meat', 'Seafood', 'Dinner', 'Italian', 'dessert']
        
        for category in main_categories:
            cursor.execute("INSERT OR IGNORE INTO tags (name, parent_id) VALUES (?, NULL)", (category,))
        
        conn.commit()
        
        # Get all tag IDs
        cursor.execute("SELECT id, name FROM tags")
        tag_map = {name: id for id, name in cursor.fetchall()}
        
        # Update parent relationships
        for child_name, parent_name in hierarchy.items():
            if child_name in tag_map and parent_name in tag_map:
                child_id = tag_map[child_name]
                parent_id = tag_map[parent_name]
                cursor.execute("UPDATE tags SET parent_id = ? WHERE id = ?", (parent_id, child_id))
                print(f"  {child_name} → {parent_name}")
        
        conn.commit()
        
        # Display the new structure
        print("\n✓ Tag hierarchy created:")
        cursor.execute("""
            SELECT 
                CASE WHEN parent_id IS NULL THEN name ELSE '  └─ ' || name END as display_name,
                parent_id
            FROM tags 
            ORDER BY 
                COALESCE(parent_id, id), 
                CASE WHEN parent_id IS NULL THEN 0 ELSE 1 END,
                name
        """)
        
        for row in cursor.fetchall():
            print(row[0])
            
    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    organize_tags()
