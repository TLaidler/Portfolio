import sqlite3
import os

def create_database():
    # Define the database file path
    db_path = os.path.join(os.path.dirname(__file__), 'stellar_occultations.db')
    
    # Connect to SQLite database (this will create the file if it doesn't exist)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create observations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_name TEXT NOT NULL,
            observation_date DATE NOT NULL,
            source_portal TEXT,
            observer_name TEXT,
            additional_metadata TEXT
        )
        ''')
        
        # Create light_curves table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS light_curves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_id INTEGER,
            time REAL NOT NULL,
            flux REAL NOT NULL,
            FOREIGN KEY (observation_id) REFERENCES observations(id)
        )
        ''')
        
        # Commit the changes
        conn.commit()
        print(f"Database created successfully at: {db_path}")
        
    except sqlite3.Error as e:
        print(f"An error occurred while creating the database: {e}")
        
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
